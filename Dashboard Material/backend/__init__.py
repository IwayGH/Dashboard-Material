from flask import Flask
import os

def create_app():
    app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
    app.config['SECRET_KEY'] = 'super_secret_key_dashboard_material_2026'
    
    # Import Blueprints
    from backend.auth import auth_bp
    from backend.routes import main_bp
    
    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    return app