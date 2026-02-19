# Localhost Testing with Biashara Pay

## Issue
Biashara Pay requires **public URLs** for webhooks and redirect URLs. `localhost` URLs are not accepted.

## Solutions

### Option 1: Use ngrok (Recommended for Testing)

1. **Install ngrok:**
   ```bash
   # macOS
   brew install ngrok
   
   # Or download from https://ngrok.com/download
   ```

2. **Start your Django server:**
   ```bash
   python manage.py runserver
   ```

3. **In another terminal, start ngrok:**
   ```bash
   ngrok http 8000
   ```

4. **Copy the ngrok URL** (e.g., `https://abc123.ngrok.io`)

5. **Update your `.env` file or settings:**
   ```env
   BASE_URL=https://abc123.ngrok.io
   ```

6. **Restart your Django server** and test again.

### Option 2: Use Your Production Domain

If you have a deployed server, use that URL:

```env
BASE_URL=https://yourdomain.com
```

### Option 3: Use a Test Domain

You can use services like:
- **ngrok** (free tier available)
- **localtunnel** (`npx localtunnel --port 8000`)
- **serveo** (`ssh -R 80:localhost:8000 serveo.net`)

## Quick Fix for Current Test

Update your `BASE_URL` in `cryptoapi/settings.py` or create a `.env` file:

```python
BASE_URL = 'https://your-ngrok-url.ngrok.io'  # Replace with your ngrok URL
```

Or in `.env`:
```env
BASE_URL=https://your-ngrok-url.ngrok.io
```

## Note

The URLs are now properly formatted with slashes. The only remaining issue is that Biashara Pay requires public URLs, not localhost.
