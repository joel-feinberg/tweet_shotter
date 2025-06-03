# Tweet Screenshot Generator - User Guide

Welcome to the Tweet Screenshot Generator! This tool allows you to easily create clean, presentation-ready images of tweets.

## Quick Start Guide

1. **Access the tool**: Open your web browser and go to http://localhost:5001 (or the URL provided by your team admin).

2. **Enter a tweet URL**: You can use tweets from either Twitter (twitter.com) or X (x.com). Just copy the URL of any public tweet.

3. **Choose a theme**:
   - **Light Mode**: White background, black text (default Twitter look)
   - **Dark Mode**: Dark blue background, white text
   - **Auto Mode**: Uses Twitter's default theme setting

4. **Optional settings**:
   - **Show engagement metrics**: Check this option to include retweet/like/view counts in the screenshot.

5. **Generate the screenshot**: Click the "Generate Screenshot" button and wait a few seconds.

5. **Download your image**: Once the screenshot is generated, you can view and download it directly from the web interface.

## Tips for Best Results

- Make sure the tweet is from a public account, not a protected account.
- The tool works with regular tweets, reply tweets, and tweets with media attachments.
- If you encounter any errors, try refreshing the page and submitting again.
- The light theme typically looks best in PowerPoint presentations against white backgrounds.

## Using the API (For Developers)

If you need to integrate this tool with other applications, you can use the API:

```
POST /api/screenshot
Content-Type: application/json

{
    "tweet_url": "https://twitter.com/username/status/123456789",
    "night_mode": 0,  // 0=light, 1=dark, 2=auto
    "show_engagement": true  // Optional: Show engagement metrics (likes, retweets, views)
}
```

The API will respond with:

```json
{
  "success": true,
  "tweet_url": "https://twitter.com/username/status/123456789",
  "screenshot_url": "http://localhost:5001/screenshots/username_123456789_20250602131959.png",
  "filename": "username_123456789_20250602131959.png"
}
```

## Troubleshooting

- **The screenshot has loading spinners**: The tweet might have embedded content that didn't finish loading. Try again.
- **Error capturing screenshot**: Make sure the tweet URL is valid and the account is public.
- **Chrome/Chromedriver errors**: Contact your team administrator - the browser driver might need updating.

## Need Help?

If you encounter any issues or have questions, please contact your team administrator.
