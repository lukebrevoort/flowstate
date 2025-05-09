from flask import Blueprint, request, jsonify
from agents.orchestrator import create_flowstate_agent
import uuid
import datetime

# Create a blueprint for chat routes
chat_bp = Blueprint('chat', __name__)

# Store threads in memory for demonstration
# In production, this would be stored in a database
threads = {}

@chat_bp.route('/threads', methods=['POST'])
def create_thread():
    """Create a new conversation thread"""
    thread_id = str(uuid.uuid4())
    threads[thread_id] = {
        'messages': [],
        'agent': create_flowstate_agent()
    }
    return jsonify({
        'thread_id': thread_id
    })

@chat_bp.route('/threads/<thread_id>/messages', methods=['GET'])
def get_messages(thread_id):
    """Get all messages in a thread"""
    if thread_id not in threads:
        return jsonify({'error': 'Thread not found'}), 404
    
    return jsonify(threads[thread_id]['messages'])

@chat_bp.route('/threads/<thread_id>/messages', methods=['POST'])
def create_message(thread_id):
    """Add a message to a thread and get the AI response"""
    if thread_id not in threads:
        return jsonify({'error': 'Thread not found'}), 404
    
    data = request.json
    content = data.get('content')
    role = data.get('role', 'user')
    
    if not content:
        return jsonify({'error': 'Message content is required'}), 400
    
    # Create user message
    user_message_id = str(uuid.uuid4())
    user_message = {
        'id': user_message_id,
        'content': content,
        'role': role,
        'created_at': str(datetime.datetime.now())
    }
    
    # Add user message to thread
    threads[thread_id]['messages'].append(user_message)
    
    # Generate AI response using the agent
    try:
        agent = threads[thread_id]['agent']
        ai_response = agent.invoke(content)
        
        # Create AI message
        ai_message_id = str(uuid.uuid4())
        ai_message = {
            'id': ai_message_id,
            'content': ai_response,
            'role': 'assistant',
            'created_at': str(datetime.datetime.now())
        }
        
        # Add AI message to thread
        threads[thread_id]['messages'].append(ai_message)
        
        return jsonify({
            'message_id': ai_message_id
        })
    except Exception as e:
        return jsonify({
            'error': f"Error generating response: {str(e)}"
        }), 500

@chat_bp.route('/threads/<thread_id>/messages/<message_id>/stream', methods=['GET'])
def stream_message(thread_id, message_id):
    """Stream an AI response for a message (for demonstration)"""
    from flask import Response
    import time
    import json
    
    if thread_id not in threads:
        return jsonify({'error': 'Thread not found'}), 404
    
    # Find the message
    message = None
    for msg in threads[thread_id]['messages']:
        if msg.get('id') == message_id:
            message = msg
            break
    
    if not message:
        return jsonify({'error': 'Message not found'}), 404
    
    def generate():
        """Generate streaming response"""
        # In a real implementation, this would stream from the actual AI response
        # For demonstration, we'll break the message into chunks
        if message['role'] == 'assistant':
            content = message['content']
            chunk_size = 10  # Characters per chunk
            
            # Stream the message in chunks
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                data = json.dumps({"type": "text", "content": chunk})
                yield f"data: {data}\n\n"
                time.sleep(0.05)  # Simulate streaming delay
                
            # Send completion signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        else:
            # If it's not an assistant message, just return it all at once
            data = json.dumps({"type": "text", "content": message['content']})
            yield f"data: {data}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')