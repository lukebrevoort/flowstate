from flask import Flask
from flask_cors import CORS
import os

# Initialize app
app = Flask(__name__)
CORS(app)

# Import database
from utils.database import Base, engine

# Import models to ensure they're registered with Base BEFORE creating tables
from models.user import User  # <-- Add this line

# Create database tables on startup 
with app.app_context():
    Base.metadata.create_all(bind=engine)

# Import blueprints - do this after app creation to avoid circular imports
from api.auth import auth_bp
from api.integrations import integrations_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(integrations_bp, url_prefix='/api')

@app.route('/api/test', methods=['GET'])
def test_route():
    return {"message": "Hello from the backend!"}

if __name__ == '__main__':
    app.run(debug=True, port=5001)