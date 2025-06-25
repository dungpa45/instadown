import requests
import os
import time
import json
import argparse
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

# Configuration

INSTAGRAM_COOKIE = os.getenv("INSTAGRAM_COOKIE")
REQUEST_DELAY = 2  # Seconds between requests to avoid blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cookie': INSTAGRAM_COOKIE
}

def create_download_directory(user_name):
    """Create download directory if it doesn't exist"""
    current_path = os.getcwd()
    download_dir = os.path.join(current_path, f"media-download/{user_name}")
    
    if not os.path.exists(download_dir):
        try:
            os.makedirs(download_dir)
            print(f"Created directory: {download_dir}")
        except Exception as e:
            print(f"Error creating directory: {e}")
            return None
    return download_dir

def download_image(url, file_path):
    """Download and save an image with error handling"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        with open(file_path, "wb") as file:
            file.write(response.content)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def download_video(url, file_path):
    """Download and save a video with error handling"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        response.raise_for_status()

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def get_instagram_data(url):
    """Make API request with error handling"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except json.JSONDecodeError:
        print("Failed to parse JSON response")
        return None

def main(ig_user_name, output_dir=None):
    # Create download directory
    download_dir = create_download_directory(ig_user_name)
    if not download_dir:
        return
    
    # Initial API request
    base_url = 'https://www.instagram.com/graphql/query'
    
    end_cursor = ""
    has_next_page = True
    total_downloaded = 0
    page_count = 0
    video_downloaded = 0
    
    while has_next_page:
        # Build URL with proper encoding
        variables = {
            "data": {
                "count": 14,
                "include_relationship_info": 'true',
                "latest_besties_reel_media": 'true',
                "latest_reel_media": 'true'
            },
            "username": ig_user_name,
            "after": end_cursor,
            "__relay_internal__pv__PolarisFeedShareMenurelayprovider": 'false'
        }
        encoded_vars = quote(json.dumps(variables))
        url = f"{base_url}?variables={encoded_vars}&doc_id=7898261790222653&server_timestamps=true"
        
        print(f"Fetching page {page_count + 1}: {url}")
        
        # Get data from Instagram
        data = get_instagram_data(url)
        if not data:
            print("Stopping due to API error")
            break
        
        # Extract page info
        try:
            timeline_media = data['data']['xdt_api__v1__feed__user_timeline_graphql_connection']
            has_next_page = timeline_media['page_info']['has_next_page']
            end_cursor = timeline_media['page_info']['end_cursor']
            edges = timeline_media['edges']
        except KeyError:
            print("Unexpected API response format")
            print(data)
            break
        
        # Process each post
        page_downloaded = 0
        for edge in edges:
            node = edge['node']
            # Carousel (multi-image) post
            if node['carousel_media']:
                print(f"Carousel detected, downloading {len(node['carousel_media'])} images")
                for child_node in node['carousel_media']:
                    if not child_node['video_versions']:
                        image_url = child_node['image_versions2']['candidates'][0]['url']
                        filename = f"{child_node['id']}.jpg"
                        file_path = os.path.join(download_dir, filename)
                        if os.path.exists(file_path):
                            print(f"File already exists: {file_path}")
                            continue
                        if download_image(image_url, file_path):
                            page_downloaded += 1
                            total_downloaded += 1
            # Single image post
            elif not node['video_versions']:
                print("Single image detected")
                image_url = node['image_versions2']['candidates'][0]['url']
                filename = f"{node['id']}.jpg"
                file_path = os.path.join(download_dir, filename)
                if os.path.exists(file_path):
                    print(f"File already exists: {file_path}")
                    continue
                if download_image(image_url, file_path):
                    page_downloaded += 1
                    total_downloaded += 1
            
            elif node['video_versions']:
                print("Video detected, let downloads the video")
                video_url = node['video_versions'][0]['url']
                filename = video_url.split('fbcdn.net/')[1].split('.mp4')[0].replace("/","_")
                file_path = os.path.join(download_dir, f"{filename}.mp4")
                if os.path.exists(file_path):
                    print(f"File already exists: {file_path}")
                    continue
                if download_video(video_url, file_path):
                    page_downloaded += 1
                    total_downloaded += 1
                    video_downloaded += 1
        
        print(f"Page {page_count + 1}: Downloaded {page_downloaded} images and {video_downloaded} videos")
        page_count += 1
        
        # Break if no more pages
        if not has_next_page:
            break
        
        # Delay between requests to avoid blocking
        time.sleep(REQUEST_DELAY)
    
    print(f"\nFinished! Downloaded {total_downloaded} images to {download_dir}")

if __name__ == "__main__":
    # main()
    parser = argparse.ArgumentParser(description='Download Instagram photos by username')
    parser.add_argument('user_name', help='Instagram User name to download photos from')
    parser.add_argument('-o', '--output', help='Output directory for downloaded photos')
    args = parser.parse_args()
    print(args)
    main(args.user_name, args.output)