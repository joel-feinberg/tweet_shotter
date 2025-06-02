# Tweet Screenshot Generator

A web application for capturing clean screenshots of tweets for presentations and other uses.

## Setup Instructions

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Download the appropriate chromedriver for your Chrome version and place it in the `drivers` directory.
   - Download from: https://chromedriver.chromium.org/downloads
   - Make sure the chromedriver version matches your Chrome browser version.

3. Run the application:
   ```
   python app.py
   ```

4. Access the web interface at http://localhost:5001

## Production Deployment

For production deployment, consider using Gunicorn as WSGI server:

1. Install Gunicorn:
   ```
   pip install gunicorn
   ```

2. Run with Gunicorn:
   ```
   gunicorn -w 4 -b 0.0.0.0:5001 app:app
   ```

3. Consider using Nginx or Apache as a reverse proxy in front of Gunicorn.

## API Usage

The application provides a simple API for programmatic access:

```
POST /api/screenshot
Content-Type: application/json

{
    "tweet_url": "https://twitter.com/username/status/123456789",
    "night_mode": 0  // 0=light, 1=dark, 2=auto
}
```

The API will return a JSON response with the URL of the generated screenshot.
