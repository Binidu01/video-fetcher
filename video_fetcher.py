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