from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
import json
import os
from video_fetcher import VideoFetcher
import logging
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'video_fetcher_secret_key'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize video fetcher
fetcher = VideoFetcher()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/fetch', methods=['POST'])
def fetch_videos():
    """API endpoint to fetch videos"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Fetch videos
        result = fetcher.fetch_videos_from_url(url)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error fetching videos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_video', methods=['POST'])
def download_video():
    """API endpoint to download a video"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        quality = data.get('quality', 'best')
        format_id = data.get('format_id')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Download video
        result = fetcher.download_video(url, quality, format_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        return jsonify({'error': str(e)}), 500

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