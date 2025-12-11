"""Flask API server for MeetingMiner."""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.pipeline import MeetingPipeline
from backend.chatbot import MeetingChatbot
from backend.database import init_db
from backend.config import Config
from backend.logger import logger
from backend.migrate_db import migrate_database

# Initialize Flask app
app = Flask(__name__, static_folder='frontend', static_url_path='')
# Enable CORS for all routes - allows all origins and methods
CORS(app)

# Serve static files
@app.route('/styles.css')
def serve_css():
    return send_from_directory('frontend', 'styles.css')

@app.route('/app.js')
def serve_js():
    return send_from_directory('frontend', 'app.js')

# Migrate database (add new columns if needed)
try:
    logger.info("Running database migration...")
    migrate_database()
    logger.info("Database migration completed.")
except Exception as e:
    logger.error(f"Migration error: {e}", exc_info=True)
    print(f"⚠️ Migration error: {e}")
    # Don't fail silently - this is important
    raise

# Initialize database
init_db()

# Initialize pipeline and chatbot
pipeline = MeetingPipeline()
chatbot = MeetingChatbot()


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('frontend', 'index.html')


@app.route('/api/meetings', methods=['GET', 'OPTIONS'])
def list_meetings():
    """List all meetings."""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
    
    try:
        meetings = pipeline.list_meetings()
        response = jsonify({"success": True, "meetings": meetings})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_msg = f"Error listing meetings: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"ERROR: {error_msg}")
        response = jsonify({"success": False, "error": error_msg})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@app.route('/api/meetings/<int:meeting_id>', methods=['GET'])
def get_meeting(meeting_id):
    """Get meeting details."""
    try:
        meeting_data = pipeline.get_meeting(meeting_id)
        if not meeting_data:
            return jsonify({"success": False, "error": "Meeting not found"}), 404
        return jsonify({"success": True, "meeting": meeting_data})
    except Exception as e:
        error_msg = f"Error retrieving meeting: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"ERROR: {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 500


@app.route('/api/meetings', methods=['POST', 'OPTIONS'])
def process_meeting():
    """Process a new meeting transcript."""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    logger.info(f"Processing meeting request: method={request.method}, content_type={request.content_type}, origin={request.headers.get('Origin')}")
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        transcript = data.get('transcript')
        title = data.get('title')
        project_name = data.get('project_name')  # User-provided project name (optional)
        transcript_json = data.get('transcript_json')
        
        if not transcript:
            return jsonify({"success": False, "error": "Transcript is required"}), 400
        
        # Process the meeting (pass user-provided project_name if available)
        result = pipeline.process(
            transcript=transcript,
            title=title,
            project_name=project_name,  # Pass user-provided project name
            transcript_json=transcript_json
        )
        
        response = jsonify({"success": True, "result": result})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_msg = f"Error processing meeting: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"ERROR: {error_msg}")
        response = jsonify({"success": False, "error": error_msg})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Query the chatbot."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        question = data.get('question')
        meeting_id = data.get('meeting_id')  # Keep for backward compatibility
        project_name = data.get('project_name')  # New: filter by project name
        
        if not question:
            return jsonify({"success": False, "error": "Question is required"}), 400
        
        # Query chatbot (use project_name if provided, otherwise fall back to meeting_id)
        chatbot_response = chatbot.query(question, meeting_id=meeting_id, project_name=project_name)
        
        response = jsonify({"success": True, "response": chatbot_response})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_msg = f"Error querying chatbot: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"ERROR: {error_msg}")
        response = jsonify({"success": False, "error": error_msg})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@app.route('/api/projects', methods=['GET', 'OPTIONS'])
def list_projects():
    """List all unique projects with meeting counts."""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
    
    try:
        from backend.database import get_db_session
        from backend.models import Meeting
        from collections import Counter
        
        db = get_db_session()
        try:
            meetings = db.query(Meeting).all()
            # Count meetings per project
            project_counts = Counter()
            for meeting in meetings:
                if meeting.project_name:
                    project_counts[meeting.project_name] += 1
            
            # Create list of projects with counts
            projects = [{"name": name, "count": count} for name, count in project_counts.items()]
            projects.sort(key=lambda x: x["count"], reverse=True)  # Sort by count descending
            
            response = jsonify({"success": True, "projects": projects})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        finally:
            db.close()
    except Exception as e:
        error_msg = f"Error listing projects: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"ERROR: {error_msg}")
        response = jsonify({"success": False, "error": error_msg})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@app.route('/api/config', methods=['GET', 'OPTIONS'])
def get_config():
    """Get application configuration."""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
    
    try:
        response = jsonify({
            "success": True,
            "config": {
                "llm_provider": Config.LLM_PROVIDER
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_msg = f"Error getting config: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"ERROR: {error_msg}")
        response = jsonify({"success": False, "error": error_msg})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

