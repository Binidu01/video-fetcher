import re
import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import yt_dlp
import validators
import logging
from typing import List, Dict, Optional, Set
import json
import os
import cv2
from PIL import Image
import base64
import io
import tempfile
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Common video file extensions
        self.video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.ogv'}
        
        # Common video hosting domains
        self.video_domains = {
            'youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com', 
            'twitch.tv', 'facebook.com', 'instagram.com', 'tiktok.com',
            'twitter.com', 'x.com', 'rumble.com', 'bitchute.com'
        }
        
        # Create downloads directory if it doesn't exist
        self.downloads_dir = 'downloads'
        os.makedirs(self.downloads_dir, exist_ok=True)

    def fetch_videos_from_url(self, url: str) -> Dict:
        """
        Main method to fetch all videos from a given URL
        """
        if not validators.url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        result = {
            'url': url,
            'videos': [],
            'errors': [],
            'methods_used': []
        }
        
        try:
            # Method 1: Parse HTML for video elements and sources
            html_videos = self._extract_from_html(url)
            if html_videos:
                result['videos'].extend(html_videos)
                result['methods_used'].append('html_parsing')
            
            # Method 2: Use yt-dlp for supported sites
            ytdlp_videos = self._extract_with_ytdlp(url)
            if ytdlp_videos:
                result['videos'].extend(ytdlp_videos)
                result['methods_used'].append('yt-dlp')
            
            # Method 3: Scan for direct video links
            direct_videos = self._find_direct_video_links(url)
            if direct_videos:
                result['videos'].extend(direct_videos)
                result['methods_used'].append('direct_links')
            
            # Remove duplicates
            result['videos'] = self._remove_duplicates(result['videos'])
            
            # Enhance video info with thumbnails and metadata
            result['videos'] = self._enhance_video_info(result['videos'])
            
        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"Error fetching videos from {url}: {e}")
        
        return result

    def _extract_from_html(self, url: str) -> List[Dict]:
        """
        Extract video URLs by parsing HTML elements
        """
        videos = []
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find video tags
            video_tags = soup.find_all('video')
            for video in video_tags:
                video_info = self._process_video_tag(video, url)
                if video_info:
                    videos.append(video_info)
            
            # Find source tags within video elements
            source_tags = soup.find_all('source')
            for source in source_tags:
                if source.get('src'):
                    video_url = urljoin(url, source.get('src'))
                    if self._is_video_url(video_url):
                        videos.append({
                            'url': video_url,
                            'type': source.get('type', 'unknown'),
                            'method': 'html_source_tag'
                        })
            
            # Find iframe embeds (YouTube, Vimeo, etc.)
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src')
                if src and self._is_video_embed(src):
                    videos.append({
                        'url': urljoin(url, src),
                        'type': 'embed',
                        'method': 'iframe_embed'
                    })
                    
        except Exception as e:
            logger.error(f"Error parsing HTML from {url}: {e}")
        
        return videos

    def _extract_with_ytdlp(self, url: str) -> List[Dict]:
        """
        Use yt-dlp to extract videos from supported sites
        """
        videos = []
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Don't download, just extract info
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    
                    if info:
                        if 'entries' in info:  # Playlist
                            for entry in info['entries']:
                                if entry:
                                    videos.append({
                                        'url': entry.get('webpage_url', entry.get('url')),
                                        'title': entry.get('title', 'Unknown'),
                                        'duration': entry.get('duration'),
                                        'view_count': entry.get('view_count'),
                                        'method': 'yt-dlp_playlist'
                                    })
                        else:  # Single video
                            videos.append({
                                'url': info.get('webpage_url', url),
                                'title': info.get('title', 'Unknown'),
                                'duration': info.get('duration'),
                                'view_count': info.get('view_count'),
                                'formats': [f.get('url') for f in info.get('formats', []) if f.get('url')],
                                'method': 'yt-dlp_single'
                            })
                            
                except yt_dlp.DownloadError:
                    # Site not supported by yt-dlp
                    pass
                    
        except Exception as e:
            logger.error(f"Error with yt-dlp for {url}: {e}")
        
        return videos

    def _find_direct_video_links(self, url: str) -> List[Dict]:
        """
        Find direct video file links on the page
        """
        videos = []
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Use regex to find video URLs in the page content
            video_patterns = [
                r'https?://[^\s<>"\']+\.(?:mp4|avi|mov|wmv|flv|webm|mkv|m4v)',
                r'src=["\']([^"\']+\.(?:mp4|avi|mov|wmv|flv|webm|mkv|m4v))["\']',
                r'url:["\']([^"\']+\.(?:mp4|avi|mov|wmv|flv|webm|mkv|m4v))["\']'
            ]
            
            content = response.text
            for pattern in video_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    video_url = match if match.startswith('http') else urljoin(url, match)
                    if self._is_video_url(video_url):
                        videos.append({
                            'url': video_url,
                            'type': 'direct',
                            'method': 'regex_extraction'
                        })
                        
        except Exception as e:
            logger.error(f"Error finding direct video links from {url}: {e}")
        
        return videos

    def _process_video_tag(self, video_tag, base_url: str) -> Optional[Dict]:
        """
        Process a video HTML tag and extract information
        """
        src = video_tag.get('src')
        if src:
            video_url = urljoin(base_url, src)
            return {
                'url': video_url,
                'poster': video_tag.get('poster'),
                'controls': video_tag.get('controls') is not None,
                'autoplay': video_tag.get('autoplay') is not None,
                'method': 'html_video_tag'
            }
        return None

    def _is_video_url(self, url: str) -> bool:
        """
        Check if URL points to a video file
        """
        try:
            parsed = urlparse(url.lower())
            # Check file extension
            if any(parsed.path.endswith(ext) for ext in self.video_extensions):
                return True
            # Check domain
            if any(domain in parsed.netloc for domain in self.video_domains):
                return True
            return False
        except:
            return False

    def _is_video_embed(self, url: str) -> bool:
        """
        Check if URL is a video embed
        """
        embed_patterns = [
            r'youtube\.com/embed/',
            r'vimeo\.com/video/',
            r'dailymotion\.com/embed/',
            r'player\.twitch\.tv/',
            r'facebook\.com/plugins/video',
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in embed_patterns)

    def _remove_duplicates(self, videos: List[Dict]) -> List[Dict]:
        """
        Remove duplicate video URLs
        """
        seen_urls = set()
        unique_videos = []
        
        for video in videos:
            url = video.get('url', '')
            if url not in seen_urls:
                seen_urls.add(url)
                unique_videos.append(video)
        
        return unique_videos

    def _enhance_video_info(self, videos: List[Dict]) -> List[Dict]:
        """
        Enhance video information with thumbnails and metadata
        """
        enhanced_videos = []
        
        for video in videos:
            try:
                # Get enhanced info using yt-dlp for supported platforms
                enhanced_info = self._get_video_metadata(video['url'])
                if enhanced_info:
                    video.update(enhanced_info)
                
                enhanced_videos.append(video)
                
            except Exception as e:
                logger.error(f"Error enhancing video info for {video.get('url')}: {e}")
                enhanced_videos.append(video)
        
        return enhanced_videos

    def _get_video_metadata(self, url: str) -> Dict:
        """
        Get enhanced metadata for a video URL using yt-dlp
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    
                    metadata = {}
                    
                    # Basic info
                    if 'title' in info:
                        metadata['title'] = info['title']
                    if 'duration' in info:
                        metadata['duration'] = info['duration']
                        metadata['duration_string'] = self._format_duration(info['duration'])
                    if 'view_count' in info:
                        metadata['view_count'] = info['view_count']
                    if 'uploader' in info:
                        metadata['uploader'] = info['uploader']
                    if 'upload_date' in info:
                        metadata['upload_date'] = info['upload_date']
                    
                    # Thumbnail
                    if 'thumbnail' in info:
                        metadata['thumbnail_url'] = info['thumbnail']
                        # Generate base64 thumbnail for display
                        thumbnail_b64 = self._get_thumbnail_base64(info['thumbnail'])
                        if thumbnail_b64:
                            metadata['thumbnail_base64'] = thumbnail_b64
                    
                    # Available formats
                    if 'formats' in info:
                        formats = []
                        for fmt in info['formats']:
                            if fmt.get('vcodec') != 'none':  # Video formats only
                                format_info = {
                                    'format_id': fmt.get('format_id'),
                                    'ext': fmt.get('ext'),
                                    'quality': fmt.get('height', 'unknown'),
                                    'filesize': fmt.get('filesize'),
                                    'url': fmt.get('url')
                                }
                                formats.append(format_info)
                        metadata['formats'] = formats
                    
                    return metadata
                    
                except yt_dlp.DownloadError:
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting metadata for {url}: {e}")
            return {}

    def _format_duration(self, seconds: int) -> str:
        """
        Format duration in seconds to HH:MM:SS format
        """
        if seconds is None:
            return "Unknown"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def _get_thumbnail_base64(self, thumbnail_url: str, max_size: tuple = (200, 150)) -> str:
        """
        Download thumbnail and convert to base64 for display
        """
        try:
            response = self.session.get(thumbnail_url, timeout=10)
            response.raise_for_status()
            
            # Open image and resize
            img = Image.open(io.BytesIO(response.content))
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/jpeg;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Error processing thumbnail {thumbnail_url}: {e}")
            return ""

    def download_video(self, url: str, quality: str = 'best', format_id: str = None) -> Dict:
        """
        Download a video from the given URL
        """
        try:
            # Sanitize filename
            ydl_opts = {
                'format': format_id if format_id else quality,
                'outtmpl': os.path.join(self.downloads_dir, '%(title)s.%(ext)s'),
                'restrictfilenames': True,
                'noplaylist': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get info first
                info = ydl.extract_info(url, download=False)
                
                # Create safe filename
                title = info.get('title', 'video')
                title = re.sub(r'[<>:"/\\|?*]', '_', title)[:100]  # Limit length
                
                # Update output template with safe filename
                ydl_opts['outtmpl'] = os.path.join(self.downloads_dir, f'{title}.%(ext)s')
                
                # Download
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                    ydl_download.download([url])
                
                # Find the downloaded file
                downloaded_files = []
                for file in os.listdir(self.downloads_dir):
                    if title in file:
                        downloaded_files.append(file)
                
                if downloaded_files:
                    filepath = os.path.join(self.downloads_dir, downloaded_files[0])
                    filesize = os.path.getsize(filepath)
                    
                    # Generate thumbnail from downloaded video
                    thumbnail_path = self._generate_video_thumbnail(filepath)
                    
                    return {
                        'success': True,
                        'filename': downloaded_files[0],
                        'filepath': filepath,
                        'filesize': filesize,
                        'filesize_mb': round(filesize / (1024 * 1024), 2),
                        'thumbnail_path': thumbnail_path,
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration'),
                        'uploader': info.get('uploader')
                    }
                else:
                    return {'success': False, 'error': 'Download completed but file not found'}
                    
        except Exception as e:
            logger.error(f"Error downloading video {url}: {e}")
            return {'success': False, 'error': str(e)}

    def _generate_video_thumbnail(self, video_path: str) -> str:
        """
        Generate thumbnail from downloaded video file
        """
        try:
            # Create thumbnail filename
            thumbnail_filename = os.path.splitext(os.path.basename(video_path))[0] + '_thumb.jpg'
            thumbnail_path = os.path.join(self.downloads_dir, thumbnail_filename)
            
            # Use OpenCV to extract frame
            cap = cv2.VideoCapture(video_path)
            
            # Get video duration and extract frame from middle
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if fps > 0:
                middle_frame = total_frames // 2
                cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Resize frame to thumbnail size
                height, width = frame.shape[:2]
                if width > 300:
                    new_width = 300
                    new_height = int(height * (new_width / width))
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # Save thumbnail
                cv2.imwrite(thumbnail_path, frame)
                return thumbnail_path
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error generating thumbnail for {video_path}: {e}")
            return ""

    async def fetch_videos_async(self, urls: List[str]) -> List[Dict]:
        """
        Asynchronously fetch videos from multiple URLs
        """
        async def fetch_single_url(session, url):
            try:
                async with session.get(url) as response:
                    content = await response.text()
                    # Simplified async version - could be expanded
                    return {'url': url, 'status': 'completed'}
            except Exception as e:
                return {'url': url, 'status': 'error', 'error': str(e)}

        async with aiohttp.ClientSession() as session:
            tasks = [fetch_single_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
            return results

if __name__ == "__main__":
    # Example usage
    fetcher = VideoFetcher()
    test_url = "https://example.com"
    result = fetcher.fetch_videos_from_url(test_url)
    print(json.dumps(result, indent=2))