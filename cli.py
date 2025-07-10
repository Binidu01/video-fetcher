#!/usr/bin/env python3
"""
Video Fetcher CLI - Command line interface for fetching videos from websites
"""

import argparse
import json
import sys
from video_fetcher import VideoFetcher
import logging

def setup_logging(verbose=False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def print_results(result, output_format='table'):
    """Print the results in the specified format"""
    if output_format == 'json':
        print(json.dumps(result, indent=2))
    elif output_format == 'table':
        print(f"\n{'='*60}")
        print(f"URL: {result['url']}")
        print(f"Videos found: {len(result['videos'])}")
        print(f"Methods used: {', '.join(result['methods_used']) if result['methods_used'] else 'None'}")
        
        if result['errors']:
            print(f"Errors: {len(result['errors'])}")
            for error in result['errors']:
                print(f"  - {error}")
        
        print(f"{'='*60}")
        
        if result['videos']:
            for i, video in enumerate(result['videos'], 1):
                print(f"\n{i}. Video:")
                print(f"   URL: {video['url']}")
                if 'title' in video:
                    print(f"   Title: {video['title']}")
                if 'duration' in video and video['duration']:
                    print(f"   Duration: {video['duration']} seconds")
                if 'method' in video:
                    print(f"   Detection method: {video['method']}")
                if 'type' in video:
                    print(f"   Type: {video['type']}")
        else:
            print("\nNo videos found.")

def save_to_file(result, filename):
    """Save results to a file"""
    try:
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {filename}")
    except Exception as e:
        print(f"Error saving to file: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Fetch all videos from a given website URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://example.com
  %(prog)s https://youtube.com/watch?v=example --format json
  %(prog)s https://example.com --output results.json --verbose
        """
    )
    
    parser.add_argument(
        'url',
        help='Website URL to fetch videos from'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['table', 'json'],
        default='table',
        help='Output format (default: table)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Save results to file (JSON format)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=10,
        help='Request timeout in seconds (default: 10)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    try:
        # Create fetcher and fetch videos
        fetcher = VideoFetcher()
        print(f"Fetching videos from: {args.url}")
        result = fetcher.fetch_videos_from_url(args.url)
        
        # Print results
        print_results(result, args.format)
        
        # Save to file if requested
        if args.output:
            save_to_file(result, args.output)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()