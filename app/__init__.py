from flask import Flask
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app()
    
    # Initialize directories
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['VECTOR_STORE_DIR'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_DIR'], exist_ok=True)

    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app