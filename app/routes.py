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
                # Generate preview
                preview_content = "Preview unavailable"
                one_page_path = os.path.join(Config.OUTPUT_DIR, 'one_page_summary.docx')
                
                try:
                    if os.path.exists(one_page_path):
                        doc = Document(one_page_path)
                        paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
                        preview_content = '\n\n'.join(paragraphs[:3]) or "Preview content empty"
                        logger.info(f"Generated preview from {one_page_path}")
                except Exception as e:
                    logger.error(f"Preview error: {str(e)}", exc_info=True)

                return jsonify({
                    'success': True,
                    'preview': preview_content,
                    'downloads': {
                        'one_page': url_for('main.download_file', filename='one_page_summary.docx'),
                        'two_page': url_for('main.download_file', filename='two_page_summary.docx')
                    }
                })

            return jsonify({'success': False, 'error': 'Processing failed'})
        
        # GET request
        return render_template('index.html')
    
    except Exception as e:
        logger.error(f"Main route error: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e))

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
    
@main_bp.route('/evaluate', methods=['GET'])
def evaluate_rag():
    try:
        # Get ground truth questions and answers from config

        evaluator = RagaEvaluator(
            vector_dir=Config.VECTOR_STORE_DIR,
            ground_truth=Config.GROUND_TRUTH,
            openai_api_key=Config.OPENAI_API_KEY
        )

        results_df = evaluator.run_evaluation()
        
        # Calculate average scores
        avg_scores = {
            'relevancy': results_df['answer_relevancy'].mean(),
            'faithfulness': results_df['faithfulness'].mean(),
            'recall': results_df['context_recall'].mean()
        }

        return jsonify(avg_scores)

    except Exception as e:
        logger.error(f"RAG evaluation failed: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500