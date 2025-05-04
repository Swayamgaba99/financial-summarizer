import os
import logging
from flask import (
    Blueprint, 
    render_template, 
    request, 
    jsonify, 
    send_from_directory,
    url_for
)
from docx import Document
from app.config import Config
from app.services.financial_processor import FinancialDocumentProcessor
from app.services.raga_evaluator import RagaEvaluator
from app.utils.file_handler import FileHandler

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

file_handler = FileHandler(
    upload_folder=Config.UPLOAD_FOLDER,
    allowed_extensions=Config.ALLOWED_EXTENSIONS
)

def get_summary_preview(docx_path):
    """Direct text extraction without formatting"""
    try:
        logger.debug(f"Preview requested for: {docx_path}")
        
        if not isinstance(docx_path, str) or not docx_path:
            logger.error("Invalid path type or empty string")
            return "Preview unavailable - invalid path"

        # 2. Verify file existence and accessibility
        if not os.path.exists(docx_path):
            logger.error(f"File not found: {os.path.abspath(docx_path)}")
            return "Preview unavailable - file not found"

        if not os.access(docx_path, os.R_OK):
            logger.error(f"Access denied to file: {docx_path}")
            return "Preview unavailable - access denied"

        # 3. Check file validity
        if not docx_path.lower().endswith('.docx'):
            logger.error(f"Invalid file extension: {os.path.splitext(docx_path)[1]}")
            return "Preview unavailable - not a DOCX file"

        file_size = os.path.getsize(docx_path)
        logger.debug(f"File size: {file_size} bytes")
        
        if file_size == 0:
            logger.error("Empty file detected")
            return "Preview unavailable - empty document"

        # 4. Attempt document parsing
        try:
            doc = Document(docx_path)
        except Exception as e:
            logger.error(f"DOCX parsing failed: {str(e)}", exc_info=True)
            return "Preview unavailable - corrupted document"

        # 5. Content analysis
        paragraphs = []
        total_paragraphs = 0
        empty_paragraphs = 0
        
        for para in doc.paragraphs:
            total_paragraphs += 1
            text = para.text.strip()
            
            if text:
                logger.debug(f"Found paragraph: {text[:100]}...")  # First 100 chars
                paragraphs.append(text)
                if len(paragraphs) >= 3:
                    break
            else:
                empty_paragraphs += 1

        logger.info(f"Paragraph stats: Total={total_paragraphs}, Empty={empty_paragraphs}, Found={len(paragraphs)}")

        # 6. Handle different content scenarios
        if not paragraphs:
            logger.warning("No text content found in document")
            
            # Check for tables
            if len(doc.tables) > 0:
                logger.warning("Document contains tables - text might be in table cells")
                return "Preview unavailable - content in tables"
                
            return "No preview content available"

        return '\n\n'.join(paragraphs)

    except Exception as e:
        logger.critical(f"Critical preview error: {str(e)}", exc_info=True)
        return "Preview unavailable - system error"
        

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    try:
        if request.method == 'POST':
            files = request.files.getlist('files')
            
            if not any(f.filename != '' for f in files):
                return render_template('error.html', error="No files selected")

            saved_files = file_handler.save_uploaded_files(files)
            
            if not saved_files:
                return render_template('error.html', error="Invalid file(s)")

            processor = FinancialDocumentProcessor(
                Config.UPLOAD_FOLDER,
                Config.OUTPUT_DIR,
                Config.OPENAI_API_KEY
            )
            
            if processor.process_documents():
                # Path to generated one-page summary
                one_page_path = os.path.join(Config.OUTPUT_DIR, 'one_page_summary.docx')
                
                return render_template('index.html',
                                    summary_preview=get_summary_preview(one_page_path),
                                    output_files={
                                        'one_page': 'one_page_summary.docx',
                                        'two_page': 'two_page_summary.docx'
                                    })
            
        return render_template('index.html')
    
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return render_template('error.html', error=str(e))

@main_bp.route('/process', methods=['POST'])
def api_process():
    try:
        files = request.files.getlist('files')
        saved_files = file_handler.save_uploaded_files(files)
        
        if not saved_files:
            return jsonify({'error': 'No valid documents'}), 400

        processor = FinancialDocumentProcessor(
            Config.UPLOAD_FOLDER,
            Config.OUTPUT_DIR,
            Config.OPENAI_API_KEY
        )
        
        if processor.process_documents():
            return jsonify({
                'download_urls': {
                    'one_page': url_for('main.download_file', filename='one_page_summary.docx'),
                    'two_page': url_for('main.download_file', filename='two_page_summary.docx')
                }
            })
        
        return jsonify({'error': 'Processing failed'}), 500

    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/download/<filename>')
def download_file(filename):
    try:
        allowed_files = {'one_page_summary.docx', 'two_page_summary.docx'}
        
        if filename not in allowed_files:
            return jsonify({'error': 'Invalid filename'}), 400
            
        return send_from_directory(
            directory=os.path.abspath(Config.OUTPUT_DIR),
            path=filename,
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'Download failed'}), 500