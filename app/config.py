import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    UPLOAD_FOLDER = 'instance/uploads'
    VECTOR_STORE_DIR = 'instance/uploads/vector_store'
    OUTPUT_DIR = 'instance/output'
    ALLOWED_EXTENSIONS = {'pdf'}
    LOG_LEVEL = 'DEBUG'  
    LOG_FILE = 'app.log'
    GROUND_TRUTH = [
            {"question": "What is the fiscal year end date for Apple as per the 10-K report?", "answer": "September 24, 2022"},
            {"question": "How many full-time equivalent employees did Apple have as of the 2022 fiscal year end?", "answer": "Approximately 164,000"},
            {"question": "What are the primary product categories mentioned in Apple's 10-K?", "answer": "iPhone, Mac, iPad, Wearables, Home and Accessories"},
            {"question": "Which services are included under AppleCare?", "answer": "Priority access to Apple technical support, repair and replacement services, and additional coverage for accidental damage, theft, and loss depending on region and product."},
            {"question": "What is the Apple Vision Pro's announced price according to the Deutsche Bank report?", "answer": "$3,499"},
            {"question": "What is the reported revenue from Services in Q2 2023 according to the 10-Q?", "answer": "$20.907 billion"},
            {"question": "What was Apple's total net income in the six months ending April 1, 2023?", "answer": "$54.158 billion"},
            {"question": "Which processor powers Apple’s Vision Pro headset?", "answer": "Apple M2 along with the new Apple R1"},
            {"question": "What is Apple’s approach to intellectual property according to the 10-K?", "answer": "Apple holds a broad portfolio including patents, trademarks, copyrights, and relies on innovation and licensing as well."}
    ]


    @classmethod
    def init_app(cls):
        """Create required directories"""
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.VECTOR_STORE_DIR, exist_ok=True)
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)