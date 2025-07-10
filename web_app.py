from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
import json
import os
from video_fetcher import VideoFetcher
import logging
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'video_fetcher_secret_key'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Initialize video fetcher
fetcher = VideoFetcher()

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error', 'success': False}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return jsonify({'error': 'An unexpected error occurred', 'success': False}), 500

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/fetch', methods=['POST'])
def fetch_videos():
    """API endpoint to fetch videos"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        logger.info(f"Fetching videos from URL: {url}")
        
        # Fetch videos
        result = fetcher.fetch_videos_from_url(url)
        
        # Ensure we always return valid JSON
        if not isinstance(result, dict):
            result = {'error': 'Invalid response format', 'videos': [], 'methods_used': []}
        
        logger.info(f"Successfully fetched {len(result.get('videos', []))} videos")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error fetching videos: {e}", exc_info=True)
        return jsonify({
            'error': str(e),
            'videos': [],
            'methods_used': [],
            'errors': [str(e)]
        }), 500

@app.route('/download_video', methods=['POST'])
def download_video():
    """API endpoint to download a video"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        if not data:
            return jsonify({'error': 'No data provided', 'success': False}), 400
            
        url = data.get('url', '').strip()
        quality = data.get('quality', 'best')
        format_id = data.get('format_id')
        
        if not url:
            return jsonify({'error': 'URL is required', 'success': False}), 400
        
        logger.info(f"Downloading video from URL: {url} with quality: {quality}")
        
        # Download video
        result = fetcher.download_video(url, quality, format_id)
        
        # Ensure we always return valid JSON with success flag
        if not isinstance(result, dict):
            result = {'error': 'Invalid response format', 'success': False}
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error downloading video: {e}", exc_info=True)
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/download_file/<filename>')
def download_file(filename):
    """Download a file from the downloads directory"""
    try:
        safe_filename = secure_filename(filename)
        downloads_dir = fetcher.downloads_dir
        
        if os.path.exists(os.path.join(downloads_dir, safe_filename)):
            return send_file(
                os.path.join(downloads_dir, safe_filename),
                as_attachment=True,
                download_name=safe_filename
            )
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/thumbnail/<filename>')
def serve_thumbnail(filename):
    """Serve thumbnail images"""
    try:
        safe_filename = secure_filename(filename)
        downloads_dir = fetcher.downloads_dir
        
        if os.path.exists(os.path.join(downloads_dir, safe_filename)):
            return send_file(os.path.join(downloads_dir, safe_filename))
        else:
            return jsonify({'error': 'Thumbnail not found'}), 404
            
    except Exception as e:
        logger.error(f"Error serving thumbnail: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/downloads')
def list_downloads():
    """List all downloaded files"""
    try:
        downloads_dir = fetcher.downloads_dir
        files = []
        
        if os.path.exists(downloads_dir):
            for filename in os.listdir(downloads_dir):
                filepath = os.path.join(downloads_dir, filename)
                if os.path.isfile(filepath) and not filename.endswith('_thumb.jpg'):
                    # Get file stats
                    stat = os.stat(filepath)
                    files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'modified': stat.st_mtime
                    })
        
        return jsonify({'files': files})
        
    except Exception as e:
        logger.error(f"Error listing downloads: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)