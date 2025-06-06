from flask import Flask, request, render_template, send_from_directory, url_for, jsonify, send_file # Added send_file
import os
import sys
import traceback 
import logging
from datetime import datetime
from werkzeug.middleware.proxy_fix import ProxyFix
import random
import io # Added for BytesIO
import uuid # For generating unique IDs for in-memory images


FLASK_RUN_PORT = 5001
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tweet_screenshotter.log')
    ]
)
logger = logging.getLogger('tweet_screenshotter')

# Add the project root to the Python path to find main.py
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

from main import run_screenshot_capture # Import the function from main.py

app = Flask(__name__)
# Support for reverse proxies (helpful when deploying behind Nginx/Apache)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Configuration for where screenshots are saved by main.py and served from by Flask
# This should be a path relative to app.py, or an absolute path.
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, 'output_screenshots') 
app.config['SCREENSHOT_FOLDER'] = SCREENSHOT_DIR
app.config['ALLOWED_EXTENSIONS'] = {'png'}

# Ensure the screenshot output directory exists
if not os.path.exists(app.config['SCREENSHOT_FOLDER']):
    try:
        os.makedirs(app.config['SCREENSHOT_FOLDER'])
        print(f"Created screenshot directory: {app.config['SCREENSHOT_FOLDER']}")
    except OSError as e:
        print(f"Error creating screenshot directory {app.config['SCREENSHOT_FOLDER']}: {e}")
        # Depending on the desired behavior, you might want to exit or raise an exception here

# SCREENSHOT_DIR and related directory creation logic can be removed if not storing files at all.
# For now, we'll keep it, as main.py might still use it for direct testing.
# However, app.py will no longer rely on it for serving images to the user.

# In-memory cache for screenshots (simple dictionary)
# For a production app, consider a more robust cache like Redis or Memcached, 
# especially if dealing with many users or needing to scale.
# Also, implement a cleanup strategy for this cache.
IMAGE_CACHE = {}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        input_mode = request.form.get('input_mode', 'single')
        try:
            night_mode_str = request.form.get('night_mode', '2')
            if night_mode_str == 'random':
                night_mode = 'random'
            else:
                night_mode = int(night_mode_str)
                if night_mode not in [0, 1, 2]:
                    night_mode = 2
        except ValueError:
            night_mode = 2 # Default to Black if conversion fails or value is invalid
        
        lang = request.form.get('lang', 'en')
        show_engagement = request.form.get('show_engagement') == 'on'
        error_message = None
        screenshots_results = [] # Renamed from screenshots to avoid confusion with image data itself
        submitted_tweet_url = None
        submitted_bulk_urls = None

        user_ip = request.remote_addr
        logger.info(f"Request from IP: {user_ip}, Mode: {input_mode}, Theme: {night_mode_str}, Lang: {lang}")

        if input_mode == 'single':
            tweet_url = request.form.get('tweet_url', '').strip()
            submitted_tweet_url = tweet_url
            logger.info(f"Single screenshot request for URL: {tweet_url}")

            if not tweet_url:
                error_message = "Please enter a Tweet URL."
            elif not (tweet_url.startswith('https://x.com/') or tweet_url.startswith('https://twitter.com/')):
                error_message = "Please enter a valid Tweet URL."
            else:
                try:
                    current_theme_for_capture = night_mode
                    if night_mode == 'random':
                        current_theme_for_capture = random.choice([0, 1, 2])
                    
                    screenshot_data = run_screenshot_capture(tweet_url, 
                                                             night_mode=current_theme_for_capture,
                                                             lang=lang,
                                                             show_engagement=show_engagement)
                    
                    if screenshot_data and screenshot_data.get('image_bytes'):
                        image_id = str(uuid.uuid4())
                        # Store the raw bytes, not the BytesIO object
                        if hasattr(screenshot_data['image_bytes'], 'getvalue'):
                            # If it's a BytesIO object, we get its value
                            image_bytes = screenshot_data['image_bytes'].getvalue()
                        else:
                            # If it's already raw bytes
                            image_bytes = screenshot_data['image_bytes']
                            
                        IMAGE_CACHE[image_id] = {
                            'bytes': image_bytes, 
                            'filename': screenshot_data['filename']
                        }
                        logger.info(f"Stored image in cache. ID: {image_id}, Filename: {screenshot_data['filename']}. Cache size: {len(IMAGE_CACHE)}")
                        screenshots_results.append({
                            'url': tweet_url,
                            'screenshot_url': url_for('serve_image', image_id=image_id),
                            'filename': screenshot_data['filename']
                        })
                        logger.info(f"Screenshot captured for {tweet_url}, image_id: {image_id}")
                    else:
                        error_message = "Failed to capture screenshot. Tweet might be protected, deleted, or an error occurred."
                        logger.error(f"Screenshot capture failed for URL: {tweet_url}")
                except Exception as e:
                    logger.error(f"Error during single screenshot capture for {tweet_url}: {e}", exc_info=True)
                    error_message = "An unexpected error occurred while generating the screenshot."
            
            # For single mode, pass the first result directly for template convenience
            single_screenshot_url = screenshots_results[0]['screenshot_url'] if screenshots_results else None
            single_filename = screenshots_results[0]['filename'] if screenshots_results else None

            return render_template('index.html',
                                  screenshot_url=single_screenshot_url, # For the single image display
                                  filename=single_filename, # For single image download
                                  screenshots=screenshots_results, # Full list (contains one item)
                                  error_message=error_message,
                                  submitted_tweet_url=submitted_tweet_url,
                                  selected_night_mode=night_mode_str, # Pass the original string for selection
                                  show_engagement=show_engagement, # Pass the engagement setting
                                  input_mode=input_mode)
        
        elif input_mode == 'bulk':
            bulk_text = request.form.get('bulk_tweet_urls', '').strip()
            submitted_bulk_urls = bulk_text
            urls_to_process = [url.strip() for url in bulk_text.split('\n') if url.strip()]
            logger.info(f"Bulk screenshot request for {len(urls_to_process)} URLs.")

            if not urls_to_process:
                error_message = "Please enter at least one Tweet URL for bulk processing."
            else:
                valid_urls = []
                invalid_url_messages = []
                for u in urls_to_process:
                    if not (u.startswith('https://x.com/') or u.startswith('https://twitter.com/')):
                        invalid_url_messages.append(f"Invalid URL: {u}")
                    else:
                        valid_urls.append(u)
                
                if invalid_url_messages:
                    error_message = "Some URLs were invalid: " + "; ".join(invalid_url_messages)
                    # Continue processing valid URLs, or stop? For now, let's just show error and stop.
                    # If you want to process valid ones, remove the return here and handle errors per URL.
                    return render_template('index.html',
                                          error_message=error_message,
                                          screenshots=screenshots_results,
                                          submitted_bulk_urls=submitted_bulk_urls,
                                          selected_night_mode=night_mode_str,
                                          show_engagement=show_engagement,
                                          input_mode=input_mode)

                for i, url in enumerate(valid_urls):
                    try:
                        current_theme_for_capture = night_mode
                        if night_mode == 'random':
                            current_theme_for_capture = i % 3 # Cycle 0, 1, 2
                        
                        screenshot_data = run_screenshot_capture(url,
                                                                 night_mode=current_theme_for_capture,
                                                                 lang=lang,
                                                                 show_engagement=show_engagement)
                        if screenshot_data and screenshot_data.get('image_bytes'):
                            image_id = str(uuid.uuid4())
                            # Store the raw bytes, not the BytesIO object
                            if hasattr(screenshot_data['image_bytes'], 'getvalue'):
                                # If it's a BytesIO object, we get its value
                                image_bytes = screenshot_data['image_bytes'].getvalue()
                            else:
                                # If it's already raw bytes
                                image_bytes = screenshot_data['image_bytes']
                                
                            IMAGE_CACHE[image_id] = {
                                'bytes': image_bytes, 
                                'filename': screenshot_data['filename']
                            }
                            logger.info(f"Stored image in cache (bulk). ID: {image_id}, Filename: {screenshot_data['filename']}. Cache size: {len(IMAGE_CACHE)}")
                            screenshots_results.append({
                                'url': url,
                                'screenshot_url': url_for('serve_image', image_id=image_id),
                                'filename': screenshot_data['filename']
                            })
                            logger.info(f"Bulk: Screenshot captured for {url}, image_id: {image_id}")
                        else:
                            screenshots_results.append({'url': url, 'error': "Failed to capture screenshot"})
                            logger.error(f"Bulk: Screenshot capture failed for URL: {url}")
                    except Exception as e:
                        logger.error(f"Error during bulk screenshot capture for {url}: {e}", exc_info=True)
                        screenshots_results.append({'url': url, 'error': "An unexpected error occurred"})
            
            return render_template('index.html',
                                  screenshots=screenshots_results,
                                  error_message=error_message,
                                  submitted_bulk_urls=submitted_bulk_urls,
                                  selected_night_mode=night_mode_str,
                                  show_engagement=show_engagement, # Pass the engagement setting
                                  input_mode=input_mode)

    # GET request
    return render_template('index.html', selected_night_mode='2', input_mode='single', show_engagement=False)


@app.route('/image/<image_id>')
def serve_image(image_id):
    logger.info(f"Attempting to serve image_id: {image_id}")
    logger.debug(f"Current IMAGE_CACHE keys: {list(IMAGE_CACHE.keys())}")
    image_data = IMAGE_CACHE.get(image_id)
    if image_data and image_data['bytes']:
        logger.info(f"Serving image_id: {image_id}, filename: {image_data['filename']}")
        # Create a new BytesIO object from the existing one
        # This ensures we have a fresh file-like object that won't be closed
        # after it's sent to the client
        try:
            # Get the image bytes as they are (might be a BytesIO object)
            if hasattr(image_data['bytes'], 'getvalue'):
                # If it's a BytesIO object, we can get its value
                image_bytes = image_data['bytes'].getvalue()
            else:
                # If it's already raw bytes
                image_bytes = image_data['bytes']
                
            # Create a fresh BytesIO object for this request
            bytes_io = io.BytesIO(image_bytes)
            
            return send_file(
                bytes_io,
                mimetype='image/png',
                as_attachment=False, # Serve inline
                download_name=image_data['filename'] # Suggested name if user saves
            )
        except Exception as e:
            logger.error(f"Error serving image {image_id}: {str(e)}")
            return "Error serving image", 500
    else:
        logger.warning(f"Image not found or data missing for image_id: {image_id}")
        return "Image not found", 404

# Remove the old /screenshots/<filename> route as it's no longer used for user-facing images
# @app.route('/screenshots/<filename>')
# def display_screenshot(filename):
#     return send_from_directory(app.config['SCREENSHOT_FOLDER'], filename)

@app.route('/api/screenshot', methods=['POST'])
def api_screenshot():
    if not request.json or 'tweet_url' not in request.json:
        return jsonify({"error": "Missing tweet_url in JSON payload"}), 400

    tweet_url = request.json['tweet_url']
    night_mode = request.json.get('night_mode', 0) # Default to 0 (Light)
    lang = request.json.get('lang', 'en') # Default to 'en'
    show_engagement = request.json.get('show_engagement', False) # Default to not showing engagement metrics

    if night_mode not in [0, 1, 2]:
        night_mode = 0 # Default to Light if invalid

    logger.info(f"API request for URL: {tweet_url}, Theme: {night_mode}, Lang: {lang}, Show engagement: {show_engagement}")

    try:
        screenshot_data = run_screenshot_capture(tweet_url, night_mode=night_mode, lang=lang, show_engagement=show_engagement)
        if screenshot_data and screenshot_data.get('image_bytes'):
            image_id = str(uuid.uuid4())
            # Store the raw bytes, not the BytesIO object
            if hasattr(screenshot_data['image_bytes'], 'getvalue'):
                # If it's a BytesIO object, we get its value
                image_bytes = screenshot_data['image_bytes'].getvalue()
            else:
                # If it's already raw bytes
                image_bytes = screenshot_data['image_bytes']
                
            IMAGE_CACHE[image_id] = {
                'bytes': image_bytes, 
                'filename': screenshot_data['filename']
            }
            logger.info(f"Stored image in cache (API). ID: {image_id}, Filename: {screenshot_data['filename']}. Cache size: {len(IMAGE_CACHE)}")
            # For API, we might return the image URL or the image data directly
            # Returning URL is consistent with the web UI
            image_url = url_for('serve_image', image_id=image_id, _external=True)
            logger.info(f"API: Screenshot captured for {tweet_url}, image_id: {image_id}, URL: {image_url}")
            return jsonify({
                "message": "Screenshot captured successfully",
                "tweet_url": tweet_url,
                "screenshot_url": image_url,
                "filename": screenshot_data['filename']
            }), 200
        else:
            logger.error(f"API: Screenshot capture failed for URL: {tweet_url}")
            return jsonify({"error": "Failed to capture screenshot"}), 500
    except Exception as e:
        logger.error(f"API error for {tweet_url}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

if __name__ == '__main__':
    # Set a secret key for session management if you plan to use sessions
    # app.secret_key = 'your_very_secret_key' 
    
    # Get port from environment or default with better error handling
    port_env = os.environ.get('FLASK_RUN_PORT')
    if port_env:
        try:
            port = int(port_env)
            print(f"Using port {port} from environment variable")
        except ValueError:
            print(f"Warning: Invalid FLASK_RUN_PORT value '{port_env}', using default {FLASK_RUN_PORT}")
            port = int(FLASK_RUN_PORT)
    else:
        port = int(FLASK_RUN_PORT)
        print(f"Using default port {port}")
    
    app.run(debug=True, host='0.0.0.0', port=port)
