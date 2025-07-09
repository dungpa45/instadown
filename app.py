import requests
import os
import time
import json
import argparse
from urllib.parse import quote
from dotenv import load_dotenv
import re
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file, after_this_request
from PIL import Image
from io import BytesIO
import cv2
import zipfile
import tempfile

load_dotenv()

# Configuration

INSTAGRAM_COOKIE = os.getenv("INSTAGRAM_COOKIE")
REQUEST_DELAY = 2  # Seconds between requests to avoid blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cookie': INSTAGRAM_COOKIE
}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'media-download'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def create_download_directory(user_name):
    """Create download directory if it doesn't exist"""
    current_path = os.getcwd()
    download_dir = os.path.join(current_path, f"media-download/{user_name}")
    
    if not os.path.exists(download_dir):
        print(f"Creating directory: {download_dir}")
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

def extract_username(input_str):
    if input_str.startswith('http'):
        pattern = r'https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.]+)/?'
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)
        return None
    return input_str.strip()

def create_thumbnail(image_data, size=(200, 200)):
    try:
        img = Image.open(BytesIO(image_data))
        img.thumbnail(size)
        output = BytesIO()
        img.save(output, format='JPEG', quality=30)
        output.seek(0)
        return output.read()
    except Exception as e:
        print(f"Thumbnail creation error: {e}")
        return None

def get_instagram_data_web(url, cookie=None):
    headers = HEADERS.copy()
    if cookie:
        headers['Cookie'] = cookie
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except json.JSONDecodeError:
        print("Failed to parse JSON response")
        return None

def create_download_directory_web(user_name):
    download_dir = os.path.join(app.config['UPLOAD_FOLDER'], user_name)
    thumbs_dir = os.path.join(download_dir, 'thumbs')
    if not os.path.exists(download_dir):
        try:
            os.makedirs(download_dir)
            print(f"Created directory: {download_dir}")
        except Exception as e:
            print(f"Error creating directory: {e}")
            return None
    if not os.path.exists(thumbs_dir):
        try:
            os.makedirs(thumbs_dir)
            print(f"Created directory: {thumbs_dir}")
        except Exception as e:
            print(f"Error creating thumbs directory: {e}")
            return None
    return download_dir

def create_video_thumbnail(video_url, size=(200, 200)):
    try:
        # Download video to memory
        response = requests.get(video_url, stream=True, timeout=15)
        response.raise_for_status()
        video_bytes = BytesIO(response.content)
        # Save to temp file for OpenCV
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
            tmp.write(video_bytes.read())
            tmp_path = tmp.name
        # Extract first frame
        vidcap = cv2.VideoCapture(tmp_path)
        success, image = vidcap.read()
        if success:
            img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            img.thumbnail(size)
            output = BytesIO()
            img.save(output, format='JPEG', quality=30)
            output.seek(0)
            os.unlink(tmp_path)
            return output.read()
        os.unlink(tmp_path)
        return None
    except Exception as e:
        print(f"Video thumbnail creation error: {e}")
        return None

def fetch_media_items_web(ig_user_name, cookie=None, max_items=99999):
    base_url = 'https://www.instagram.com/graphql/query'
    end_cursor = ""
    has_next_page = True
    media_items = []
    page_count = 0
    while has_next_page and len(media_items) < max_items:
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
        data = get_instagram_data_web(url, cookie)
        if not data:
            break
        try:
            timeline_media = data['data']['xdt_api__v1__feed__user_timeline_graphql_connection']
            has_next_page = timeline_media['page_info']['has_next_page']
            end_cursor = timeline_media['page_info']['end_cursor']
            edges = timeline_media['edges']
        except KeyError:
            break
        for edge in edges:
            node = edge['node']
            # Carousel (multi-image) post
            if node.get('carousel_media'):
                for child_node in node['carousel_media']:
                    if child_node.get('video_versions'):
                        video_url = child_node['video_versions'][0]['url']
                        media_items.append({
                            'type': 'video',
                            'url': video_url,
                            'id': child_node['id']
                        })
                    elif not child_node.get('video_versions'):
                        image_url = child_node['image_versions2']['candidates'][0]['url']
                        media_items.append({
                            'type': 'image',
                            'url': image_url,
                            'id': child_node['id']
                        })
            # Single image post
            elif not node.get('video_versions'):
                image_url = node['image_versions2']['candidates'][0]['url']
                media_items.append({
                    'type': 'image',
                    'url': image_url,
                    'id': node['id']
                })
            # Single video post
            elif node.get('video_versions'):
                video_url = node['video_versions'][0]['url']
                media_items.append({
                    'type': 'video',
                    'url': video_url,
                    'id': node['id']
                })
            if len(media_items) >= max_items:
                break
        page_count += 1
        time.sleep(REQUEST_DELAY)
    return media_items[:max_items]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        cookie = request.form.get('cookie', '')
        clean_username = extract_username(username)
        if not clean_username:
            return render_template('index.html', error="Invalid username or URL")
        # Create user-specific download directory
        download_dir = create_download_directory_web(clean_username)
        if not download_dir:
            return render_template('index.html', error="Could not create download directory.")
        # Download media using the same logic as main
        media_items = fetch_media_items_web(clean_username, cookie)
        if not media_items:
            return render_template('index.html', error="No media found or failed to download")
        # Process media and create thumbnails
        processed_items = []
        for item in media_items:
            try:
                if item['type'] == 'image':
                    response = requests.get(item['url'], timeout=10)
                    if response.status_code != 200:
                        continue
                    original_data = response.content
                    # Save high-quality image
                    original_filename = f"{item['id']}.jpg"
                    original_filepath = os.path.join(download_dir, original_filename)
                    with open(original_filepath, 'wb') as f:
                        f.write(original_data)
                    # Create and save low-quality thumbnail in thumbs folder
                    thumbs_dir = os.path.join(download_dir, 'thumbs')
                    thumbnail_data = create_thumbnail(original_data)
                    if thumbnail_data:
                        thumb_filename = f"{item['id']}_thumb.jpg"
                        thumb_filepath = os.path.join(thumbs_dir, thumb_filename)
                        with open(thumb_filepath, 'wb') as f:
                            f.write(thumbnail_data)
                        processed_items.append({
                            'id': item['id'],
                            'thumb': f"{clean_username}/thumbs/{thumb_filename}",
                            'original': f"{clean_username}/{original_filename}",
                            'type': 'image'
                        })
                elif item['type'] == 'video':
                    # Download high-quality video file
                    video_response = requests.get(item['url'], timeout=30, stream=True)
                    if video_response.status_code != 200:
                        continue
                    video_filename = f"{item['id']}.mp4"
                    video_filepath = os.path.join(download_dir, video_filename)
                    with open(video_filepath, 'wb') as f:
                        for chunk in video_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    # Create and save video thumbnail in thumbs folder
                    thumbs_dir = os.path.join(download_dir, 'thumbs')
                    thumbnail_data = create_video_thumbnail(item['url'])
                    if thumbnail_data:
                        vthumb_filename = f"{item['id']}_vthumb.jpg"
                        vthumb_filepath = os.path.join(thumbs_dir, vthumb_filename)
                        with open(vthumb_filepath, 'wb') as f:
                            f.write(thumbnail_data)
                        processed_items.append({
                            'id': item['id'],
                            'thumb': f"{clean_username}/thumbs/{vthumb_filename}",
                            'original': f"{clean_username}/{video_filename}",
                            'type': 'video'
                        })
            except Exception as e:
                print(f"Error processing media: {e}")
        return render_template('results.html', media_items=processed_items)
    return render_template('index.html')

@app.route('/media-download/<path:filename>')
def media_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/clear')
def clear_media():
    for user_folder in os.listdir(app.config['UPLOAD_FOLDER']):
        user_path = os.path.join(app.config['UPLOAD_FOLDER'], user_folder)
        if os.path.isdir(user_path):
            for filename in os.listdir(user_path):
                file_path = os.path.join(user_path, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
            try:
                os.rmdir(user_path)
            except Exception as e:
                print(f"Error deleting folder {user_path}: {e}")
    return redirect(url_for('index'))

@app.route('/download-zip', methods=['POST'])
def download_zip():
    selected_files = request.form.getlist('selected_files')
    if not selected_files:
        return redirect(url_for('index'))
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    with zipfile.ZipFile(temp_zip, 'w') as zipf:
        for rel_path in selected_files:
            abs_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_path)
            if os.path.isfile(abs_path):
                arcname = os.path.basename(abs_path)
                zipf.write(abs_path, arcname)
    temp_zip.close()
    @after_this_request
    def cleanup(response):
        try:
            os.remove(temp_zip.name)
        except Exception:
            pass
        return response
    return send_file(temp_zip.name, as_attachment=True, download_name='instagram_media.zip', mimetype='application/zip')

@app.route('/results')
def results():
    media_items = session.get('media_items')
    if media_items:
        media_items = json.loads(media_items)
    else:
        media_items = []
    # Pagination
    if media_items:
        page = int(request.args.get('page', 1))
        per_page = 20
        total_items = len(media_items)
        total_pages = (total_items + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        paginated_items = media_items[start:end]
    else:
        page = 1
        total_pages = 1
        total_items = 0
        paginated_items = []
    return render_template('results.html', media_items=paginated_items, page=page, total_pages=total_pages, total_items=total_items)

# Remove CLI code
if __name__ == '__main__':
    app.run(debug=True)