from flask import Blueprint, render_template, request, send_from_directory
from app.services.financial_processor import FinancialDocumentProcessor
from app.config import Config
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle file upload
        for file in request.files.getlist('files'):
            file.save(os.path.join(Config.UPLOAD_FOLDER, file.filename))
        
        # Process documents
        processor = FinancialDocumentProcessor(
            Config.UPLOAD_FOLDER,
            Config.OUTPUT_DIR,
            Config.OPENAI_API_KEY
        )
        
        if processor.process_documents():
            return render_template('results.html')
        return render_template('error.html')
    return render_template('index.html')

@main_bp.route('/download/<filename>')
def download(filename):
    return send_from_directory(Config.OUTPUT_DIR, filename)