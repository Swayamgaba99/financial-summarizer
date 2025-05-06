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
                {
                "question": "What were Apple’s total net sales for fiscal 2023?",
                "answer": "Apple reported total net sales of $383.3 billion for fiscal 2023."  # From 10-K
                },
                {
                "question": "How much did Apple spend on research and development in fiscal 2023?",
                "answer": "Apple spent $29.9 billion on research and development in fiscal 2023."  # From 10-K
                },
                {
                "question": "What was Apple's Q2 2023 revenue?",
                "answer": "Apple's Q2 2023 revenue was $94.8 billion."  # From 10-Q
                },
                {
                "question": "Which geographies experienced revenue decline in Q2 2023?",
                "answer": "Revenue declined in Americas, Europe, and Greater China."  # From 10-Q
                },
                {
                "question": "What was Apple's gross margin in Q2 2023?",
                "answer": "The gross margin was 44.3% in Q2 2023."  # From 10-Q
                },
                {
                "question": "What is the name of Apple's mixed reality headset announced at WWDC?",
                "answer": "Apple's mixed reality headset is named Vision Pro."  # From Deutsche or JPM
                },
                {
                "question": "What operating system does Apple Vision Pro use?",
                "answer": "It uses a new operating system called visionOS."  # From Deutsche
                },
                {
                "question": "What is the expected price of the Apple Vision Pro headset?",
                "answer": "The expected price of the Vision Pro headset is $3,499."  # From Deutsche or JPM
                },
                {
                "question": "How does Apple differentiate between AR and VR in Vision Pro?",
                "answer": "Vision Pro offers a seamless transition between AR and VR experiences using a digital crown."  # From JPM
                },
                {
                "question": "What display technology is used in Vision Pro?",
                "answer": "Vision Pro features dual 4K micro-OLED displays."  # From Deutsche or JPM
                },
                {
                "question": "What chip powers the Apple Vision Pro?",
                "answer": "It uses Apple’s custom M2 chip along with a new R1 chip for real-time sensor processing."  # From JPM
                },
                {
                "question": "What services are integrated with the Vision Pro headset?",
                "answer": "Vision Pro supports Apple TV, Apple Music, Apple Arcade, and FaceTime natively."  # From Deutsche
                },
                {
                "question": "What are some use cases Apple highlighted for the Vision Pro?",
                "answer": "Use cases include productivity, immersive entertainment, and spatial FaceTime."  # From Deutsche
                },
                {
                "question": "What was Apple’s capital return to shareholders in fiscal 2023?",
                "answer": "Apple returned $77.6 billion to shareholders in fiscal 2023 through dividends and share repurchases."  # From 10-K
                },
                {
                "question": "What are the charging and battery details of the Vision Pro headset?",
                "answer": "The Vision Pro has a separate battery pack with approximately 2 hours of usage per charge."  # From JPM
                },
                {
                "question": "Who supplies the cameras for the Vision Pro?",
                "answer": "Sony is believed to supply the cameras and sensors for Vision Pro."  # From Deutsche
                },
                {
                "question": "What is Apple's expected product pipeline direction with Vision Pro?",
                "answer": "Apple plans to introduce more affordable AR/VR headsets in the coming years following Vision Pro."  
                }
    ]