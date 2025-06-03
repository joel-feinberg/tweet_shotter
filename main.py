import asyncio
from tweetcapture import TweetCapture
from datetime import datetime
import traceback
import os
import io # Added for in-memory file handling
import tempfile # Added for temporary file creation

# Define the path to chromedriver.
# Create a 'drivers' directory in your project root and place chromedriver there,
# or ensure chromedriver is in your system PATH.
CHROMEDRIVER_PATH = os.path.join(os.path.dirname(__file__), 'drivers', 'chromedriver')

async def capture_tweet_screenshot(tweet_url, debug=False, night_mode=0, lang='en', show_engagement=False): # Removed output_dir
    """
    Captures a screenshot of a tweet using TweetCapture.

    Parameters:
    tweet_url (str): The URL of the tweet to capture.
    debug (bool): If True, prints detailed error information.
    night_mode (int): Sets the theme (0 = Light, 1 = Dark, 2 = Black).
    lang (str): Language code for the tweet display (e.g., 'en' for English, 'es' for Spanish).
    show_engagement (bool): If True, shows engagement metrics (retweets/likes/views).

    Returns:
    dict: A dictionary containing 'image_bytes' (io.BytesIO object) and 
          'filename' (str, suggested filename for download), or None if there was an error.
    """
    # Set mode based on show_engagement parameter:
    # Mode 1 or 2 shows engagement metrics, Mode 4 (default) hides them
    mode = 1 if show_engagement else 4
    wait_time = 1.0
    radius = 10
    scale = 1.0
    show_parent_tweets = False
    show_mentions = 0
    overwrite = True # Overwrite in temp context is fine
    hide_all_media = False
    gui = False

    tweet_capture_instance = TweetCapture(
        mode,
        night_mode,
        show_parent_tweets=show_parent_tweets,
        show_mentions_count=show_mentions,
        overwrite=overwrite,
        radius=radius,
        scale=scale
    )
    tweet_capture_instance.set_lang(lang)
    tweet_capture_instance.set_wait_time(wait_time)
    if hide_all_media:
        tweet_capture_instance.hide_all_media()
    tweet_capture_instance.set_gui(gui)

    if os.path.exists(CHROMEDRIVER_PATH):
        tweet_capture_instance.set_chromedriver_path(CHROMEDRIVER_PATH)
    else:
        print(f"Warning: Chromedriver not found at {CHROMEDRIVER_PATH}. Using PATH.")

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    try:
        url_parts = tweet_url.split('/')
        tweet_identifier = "tweet"
        if len(url_parts) > 3 and url_parts[-2] == "status":
            tweet_identifier = f"{url_parts[-3]}_{url_parts[-1]}"
        elif len(url_parts) > 1:
            tweet_identifier = url_parts[-1] if url_parts[-1] else url_parts[-2]
        tweet_identifier = tweet_identifier.split('?')[0]
    except IndexError:
        tweet_identifier = "tweet"
    
    suggested_filename = f"{tweet_identifier}_{timestamp}.png"

    temp_output_filename = None # Initialize for the finally block
    try:
        # Use mkstemp for more robust temporary file handling
        tmp_fd, temp_output_filename = tempfile.mkstemp(suffix=".png")
        # We have the path, close the file descriptor so tweet-capture can open it by name
        os.close(tmp_fd) 
        
        print(f"Attempting to capture {tweet_url} to temporary file {temp_output_filename} with night_mode: {night_mode}, lang: {lang}")
        
        # TweetCapture saves the file here
        await tweet_capture_instance.screenshot(tweet_url, temp_output_filename)
        print(f"Screenshot temporarily saved: {temp_output_filename}")

        # Read the file into memory
        with open(temp_output_filename, 'rb') as f_read:
            image_bytes = f_read.read()
        
        image_bytes_io = io.BytesIO(image_bytes)
        # A new BytesIO object is already at position 0, so seek(0) is not strictly needed here.

        print(f"Screenshot read into memory for {tweet_url}, size: {len(image_bytes)} bytes")
        if len(image_bytes) < 1000: # Check for unusually small files
             print(f"WARNING: Screenshot for {tweet_url} is very small ({len(image_bytes)} bytes). This might indicate a capture error.")

        return {'image_bytes': image_bytes_io, 'filename': suggested_filename}

    except Exception as error:
        print(f"Error capturing tweet: {tweet_url}")
        if debug:
            print("Detailed error:")
            traceback.print_exc()
        else:
            print(f"Error details: {str(error)}")
        return None
    finally:
        if temp_output_filename and os.path.exists(temp_output_filename):
            try:
                os.remove(temp_output_filename)
                print(f"Temporary file {temp_output_filename} deleted.")
            except Exception as e:
                print(f"Error deleting temporary file {temp_output_filename}: {e}")

def run_screenshot_capture(tweet_url, night_mode=0, lang='en', show_engagement=False): # Removed output_dir
    """
    Synchronous wrapper to run the async screenshot capture.
    Returns a dict with image_bytes and filename, or None.
    
    Parameters:
    tweet_url (str): The URL of the tweet to capture.
    night_mode (int): Sets the theme (0 = Light, 1 = Dark, 2 = Black).
    lang (str): Language code for the tweet display.
    show_engagement (bool): If True, shows engagement metrics (retweets/likes/views).
    """
    print(f"Starting screenshot capture for {tweet_url} with night_mode: {night_mode}, lang: {lang}, show_engagement: {show_engagement}")
    result = asyncio.run(capture_tweet_screenshot(tweet_url, debug=True, night_mode=night_mode, lang=lang, show_engagement=show_engagement))
    
    if result and result['image_bytes']:
        print(f"Screenshot successfully captured in memory for {tweet_url}, suggested filename: {result['filename']}")
    else:
        print(f"Failed to capture screenshot for {tweet_url}")
    return result

if __name__ == '__main__':
    list_of_tweet_urls = [
        # "https://x.com/elonmusk/status/1795593890304692439"
    ]

    if list_of_tweet_urls:
        # This part is mostly for local testing of main.py, 
        # it will save files locally if run directly.
        # For the web app, the bytes are handled by app.py.
        main_output_dir = "output_screenshots_main_test" 
        if not os.path.exists(main_output_dir):
            os.makedirs(main_output_dir)

        night_mode_cycle = [0, 1, 2]
        current_night_mode_index = 0

        print("Starting tweet screenshotting process (main.py direct test)...")
        for url in list_of_tweet_urls:
            current_night_mode = night_mode_cycle[current_night_mode_index % len(night_mode_cycle)]
            print(f"Processing URL: {url} with night_mode {current_night_mode}")
            # output_dir is no longer a param for run_screenshot_capture
            screenshot_data = run_screenshot_capture(url, night_mode=current_night_mode, show_engagement=True) # Test with engagement metrics
            
            if screenshot_data and screenshot_data['image_bytes']:
                # For testing main.py directly, save the file
                save_path = os.path.join(main_output_dir, screenshot_data['filename'])
                with open(save_path, 'wb') as f:
                    f.write(screenshot_data['image_bytes'].read())
                print(f"Test: Saved {screenshot_data['filename']} to {main_output_dir}")
                screenshot_data['image_bytes'].seek(0) # Reset for any further reads if needed
            current_night_mode_index += 1
        
        print(f"All screenshots processed. Check the '{main_output_dir}' folder if main.py was run directly with URLs.")
    else:
        print("No URLs provided in main.py for direct testing.")

