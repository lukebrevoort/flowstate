from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import os
from functools import wraps

# Import your database and user model
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.database import SessionLocal
from models.user import User

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-for-development')
TOKEN_EXPIRATION = 24 * 60 * 60  # 24 hours in seconds

# Token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"message": "Invalid token format"}), 401
        
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        
        # Validate token
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            db = SessionLocal()
            current_user = db.query(User).filter_by(id=data['user_id']).first()
            db.close()
            
            if not current_user:
                return jsonify({"message": "User not found"}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required field: {field}"}), 400
    
    db = SessionLocal()
    
    # Check if user exists
    if db.query(User).filter_by(email=data['email']).first():
        db.close()
        return jsonify({"message": "Email already registered"}), 409
    
    # Create new user
    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        name=data['name'],
        email=data['email'],
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create token
    token = jwt.encode({
        'user_id': new_user.id,
        'exp': datetime.utcnow() + timedelta(seconds=TOKEN_EXPIRATION)
    }, SECRET_KEY, algorithm="HS256")
    
    db.close()
    
    return jsonify({
        "message": "User created successfully",
        "token": token,
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Missing email or password"}), 400
    
    db = SessionLocal()
    user = db.query(User).filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.hashed_password, data['password']):
        db.close()
        return jsonify({"message": "Invalid email or password"}), 401
    
    # Create token
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(seconds=TOKEN_EXPIRATION)
    }, SECRET_KEY, algorithm="HS256")
    
    db.close()
    
    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }), 200

@auth_bp.route('/user', methods=['GET'])
@token_required
def get_user(current_user):
    return jsonify({
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "notion_connected": bool(current_user.notion_token),
        "google_calendar_connected": bool(current_user.google_calendar_token)
    }), 200