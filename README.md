# Video Fetcher

A powerful web scraping tool that can extract all videos from any given website URL. This application uses multiple detection methods to find videos including HTML parsing, yt-dlp integration, and direct link scanning.

## Features

- **Multiple Detection Methods**: Uses HTML parsing, yt-dlp, and regex patterns to find videos
- **Wide Format Support**: Detects MP4, AVI, MOV, WMV, FLV, WebM, MKV, M4V, 3GP, OGV
- **Popular Platform Support**: Works with YouTube, Vimeo, Dailymotion, Twitch, Facebook, Instagram, TikTok, Twitter, and more
- **Web Interface**: Beautiful, modern web UI for easy interaction
- **CLI Tool**: Command-line interface for automation and scripting
- **Export Features**: Export results as JSON or copy URLs to clipboard
- **Error Handling**: Comprehensive error reporting and logging

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd video-fetcher
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Web Interface

1. Start the web server:
```bash
python web_app.py
```

2. Open your browser and go to `http://localhost:5000`

3. Enter a website URL and click "Fetch Videos"

4. View the results, copy URLs, or export as JSON

### Command Line Interface

Basic usage:
```bash
python cli.py https://example.com
```

With options:
```bash
# Output as JSON
python cli.py https://example.com --format json

# Save results to file
python cli.py https://example.com --output results.json

# Enable verbose logging
python cli.py https://example.com --verbose

# Set custom timeout
python cli.py https://example.com --timeout 15
```

### Python API

```python
from video_fetcher import VideoFetcher

# Create fetcher instance
fetcher = VideoFetcher()

# Fetch videos from URL
result = fetcher.fetch_videos_from_url('https://example.com')

# Print results
print(f"Found {len(result['videos'])} videos")
for video in result['videos']:
    print(f"- {video['url']}")
```

## How It Works

The Video Fetcher uses three main detection methods:

### 1. HTML Parsing
- Scans for `<video>` tags and their `src` attributes
- Finds `<source>` tags within video elements
- Detects iframe embeds from popular video platforms
- Extracts video metadata like poster images and controls

### 2. yt-dlp Integration
- Uses the powerful yt-dlp library for supported sites
- Extracts video information including titles, durations, and view counts
- Handles playlists and single videos
- Supports hundreds of video platforms

### 3. Direct Link Scanning
- Uses regex patterns to find direct video file URLs
- Scans page content for video file extensions
- Detects video URLs in JavaScript variables and attributes

## Supported Video Formats

- **Video Files**: MP4, AVI, MOV, WMV, FLV, WebM, MKV, M4V, 3GP, OGV
- **Platforms**: YouTube, Vimeo, Dailymotion, Twitch, Facebook, Instagram, TikTok, Twitter/X, Rumble, BitChute

## API Response Format

```json
{
  "url": "https://example.com",
  "videos": [
    {
      "url": "https://example.com/video.mp4",
      "title": "Video Title",
      "duration": 120,
      "method": "html_video_tag",
      "type": "video/mp4"
    }
  ],
  "methods_used": ["html_parsing", "yt-dlp"],
  "errors": []
}
```

## Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
# Web server settings
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False

# Request settings
REQUEST_TIMEOUT=10
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

### Custom User Agent

You can customize the User-Agent string used for requests by modifying the `VideoFetcher` class initialization.

## Error Handling

The application includes comprehensive error handling:

- **Invalid URLs**: Validates URLs before processing
- **Network Errors**: Handles timeouts and connection issues
- **Parsing Errors**: Graceful handling of malformed HTML
- **Rate Limiting**: Respects server rate limits

## Limitations

- Some websites may block automated requests
- JavaScript-heavy sites might not be fully parsed
- Rate limiting may affect performance on some sites
- Some video platforms have anti-scraping measures

## Legal Notice

This tool is for educational and research purposes only. Always respect:
- Website terms of service
- Copyright laws
- Privacy policies
- Rate limiting and robot.txt files

Users are responsible for ensuring their use complies with applicable laws and regulations.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Dependencies

- `requests`: HTTP library for making web requests
- `beautifulsoup4`: HTML parsing library
- `yt-dlp`: Video extraction library
- `flask`: Web framework for the UI
- `aiohttp`: Async HTTP client
- `validators`: URL validation
- `lxml`: XML and HTML parser

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
2. **Network Timeouts**: Increase timeout value or check internet connection
3. **No Videos Found**: Website might use JavaScript loading or have anti-scraping measures
4. **Permission Errors**: Make sure you have write permissions for output files

### Debug Mode

Enable verbose logging to troubleshoot issues:

```bash
python cli.py https://example.com --verbose
```

## Support

For questions, issues, or feature requests, please:
1. Check the existing issues
2. Create a new issue with detailed information
3. Include error messages and steps to reproduce

---

**Note**: This tool is designed for legitimate research and educational purposes. Please use responsibly and respect website terms of service.