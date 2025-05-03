import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    UPLOAD_FOLDER = 'instance/uploads'
    VECTOR_STORE_DIR = 'instance/vector_store'
    OUTPUT_DIR = 'instance/output'
    ALLOWED_EXTENSIONS = {'pdf'}

    @classmethod
    def init_app(cls):
        """Create required directories"""
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.VECTOR_STORE_DIR, exist_ok=True)
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)