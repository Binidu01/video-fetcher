from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
from video_fetcher import VideoFetcher
import logging

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

@app.route('/download')
def download_results():
    """Download results as JSON file"""
    # This would be implemented to allow downloading results
    pass

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)