from flask import Blueprint, request, jsonify
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.auth import token_required
from agents.orchestrator import run_conversation
from utils.database import SessionLocal
from models.user import User

# Import your existing NotionAPI
try:
    from agents.notion_api import NotionAPI
except ImportError:
    print("NotionAPI import failed, but proceeding")

integrations_bp = Blueprint('integrations', __name__)

@integrations_bp.route('/chat', methods=['POST'])
@token_required
def chat(current_user):
    data = request.get_json()
    if not data or not data.get('message'):
        return jsonify({"error": "Message is required"}), 400
    
    # Process messages through your orchestrator
    try:
        # Get the actual response from the run_conversation function
        result = run_conversation(data['message'])
        
        # Return the actual agent response
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@integrations_bp.route('/notion/connect', methods=['POST'])
@token_required
def connect_notion(current_user):
    data = request.get_json()
    if not data or not data.get('token'):
        return jsonify({"error": "Notion token is required"}), 400
    
    try:
        # Update user's notion token in database
        db = SessionLocal()
        user = db.query(User).filter_by(id=current_user.id).first()
        user.notion_token = data['token']
        db.commit()
        db.close()
        
        return jsonify({"message": "Notion connected successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500