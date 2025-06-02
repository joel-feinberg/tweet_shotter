#!/usr/bin/env python3
"""
Example script for programmatically using the Tweet Screenshot Generator API.
This can be used to batch process multiple tweet URLs.
"""

import requests
import json
import time
import argparse
import os
import sys
from datetime import datetime

def capture_tweet_screenshot(url, api_endpoint, night_mode=0):
    """
    Capture a tweet screenshot using the Tweet Screenshot Generator API.
    
    Args:
        url (str): The tweet URL to capture
        api_endpoint (str): The API endpoint URL
        night_mode (int): Theme mode (0=light, 1=dark, 2=auto)
        
    Returns:
        dict: API response or None if failed
    """
    headers = {
        'Content-Type': 'application/json',
    }
    
    data = {
        'tweet_url': url,
        'night_mode': night_mode
    }
    
    try:
        response = requests.post(api_endpoint, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return None

def download_screenshot(screenshot_url, output_dir, filename=None):
    """
    Download a screenshot from the provided URL.
    
    Args:
        screenshot_url (str): URL of the screenshot
        output_dir (str): Directory to save the screenshot
        filename (str, optional): Custom filename, if None, use the original filename
        
    Returns:
        str: Path to the downloaded file or None if failed
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        if filename is None:
            # Extract filename from URL
            filename = screenshot_url.split('/')[-1]
        
        output_path = os.path.join(output_dir, filename)
        
        # Download the file
        response = requests.get(screenshot_url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Download complete: {output_path}")
            return output_path
        else:
            print(f"Failed to download: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading screenshot: {str(e)}")
        return None

def process_tweet_list(tweet_file, api_endpoint, output_dir, night_mode=0, delay=1):
    """
    Process a list of tweets from a file.
    
    Args:
        tweet_file (str): Path to a file containing tweet URLs, one per line
        api_endpoint (str): API endpoint URL
        output_dir (str): Directory to save screenshots
        night_mode (int): Theme mode
        delay (int): Delay between requests in seconds
    """
    with open(tweet_file, 'r') as f:
        tweet_urls = [line.strip() for line in f.readlines() if line.strip()]
    
    print(f"Processing {len(tweet_urls)} tweets...")
    
    results = {
        'success': [],
        'failed': []
    }
    
    for idx, url in enumerate(tweet_urls, 1):
        print(f"[{idx}/{len(tweet_urls)}] Processing: {url}")
        
        response = capture_tweet_screenshot(url, api_endpoint, night_mode)
        
        if response and response.get('success'):
            screenshot_url = response.get('screenshot_url')
            filename = response.get('filename')
            
            saved_path = download_screenshot(screenshot_url, output_dir)
            
            if saved_path:
                results['success'].append({
                    'url': url,
                    'saved_path': saved_path
                })
            else:
                results['failed'].append({
                    'url': url,
                    'reason': 'Download failed'
                })
        else:
            results['failed'].append({
                'url': url,
                'reason': 'API error'
            })
            
        if idx < len(tweet_urls):
            print(f"Waiting {delay} seconds before next request...")
            time.sleep(delay)
    
    # Print summary
    print("\n===== Results =====")
    print(f"Total tweets: {len(tweet_urls)}")
    print(f"Successful: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")
    
    if results['failed']:
        print("\nFailed URLs:")
        for item in results['failed']:
            print(f"- {item['url']} ({item['reason']})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tweet Screenshot Generator CLI")
    parser.add_argument("--url", help="Single tweet URL to capture")
    parser.add_argument("--file", help="File containing tweet URLs (one per line)")
    parser.add_argument("--server", default="http://localhost:5001", help="Server URL")
    parser.add_argument("--output", default="downloaded_screenshots", help="Output directory")
    parser.add_argument("--mode", type=int, choices=[0, 1, 2], default=0, help="Theme mode (0=light, 1=dark, 2=auto)")
    parser.add_argument("--delay", type=int, default=1, help="Delay between requests in seconds")
    
    args = parser.parse_args()
    
    api_endpoint = f"{args.server}/api/screenshot"
    
    if not (args.url or args.file):
        parser.print_help()
        sys.exit(1)
        
    if args.url:
        print(f"Capturing screenshot for: {args.url}")
        response = capture_tweet_screenshot(args.url, api_endpoint, args.mode)
        
        if response and response.get('success'):
            screenshot_url = response.get('screenshot_url')
            print(f"Screenshot URL: {screenshot_url}")
            
            saved_path = download_screenshot(screenshot_url, args.output)
            if saved_path:
                print(f"Screenshot saved to: {saved_path}")
        else:
            print("Failed to capture screenshot")
            
    elif args.file:
        process_tweet_list(args.file, api_endpoint, args.output, args.mode, args.delay)
