# How to Run MeetingMiner

## Important Note

**DO NOT run `app.js` with Node.js!** The `app.js` file is browser-side JavaScript and must be loaded in a web browser.

## Method 1: Using Flask Server (Recommended)

The Flask server serves both the API and the frontend files.

1. **Start the Flask server:**
   ```bash
   python api.py
   ```
   Or:
   ```bash
   python run.py
   ```

2. **Open your browser:**
   Navigate to: `http://127.0.0.1:5000`

The Flask server will:
- Serve the HTML, CSS, and JavaScript files
- Provide the API endpoints at `/api/*`
- Handle CORS automatically

## Method 2: Using a Simple HTTP Server (Alternative)

If you want to test the frontend separately (but you still need the Flask API running):

1. **Start Flask API** (in one terminal):
   ```bash
   python api.py
   ```

2. **Start a simple HTTP server** (in another terminal):
   ```bash
   # Python 3
   cd frontend
   python -m http.server 8000
   
   # Or using Node.js http-server (if installed)
   npx http-server frontend -p 8000
   ```

3. **Open your browser:**
   Navigate to: `http://localhost:8000`

**Note:** When using a separate HTTP server, make sure CORS is enabled in `api.py` (which it already is).

## Method 3: Open HTML File Directly (Not Recommended)

You can open `frontend/index.html` directly in your browser, but:
- The API calls will work if Flask is running on `http://127.0.0.1:5000`
- Some browsers may block local file access for security reasons
- CORS should still work since we've configured it

## Troubleshooting

### Error: "Cannot connect to backend API"
- Make sure Flask server is running: `python api.py`
- Check that it's running on port 5000
- Verify the API_BASE URL in `frontend/app.js` matches your Flask server address

### Error: "document is not defined"
- You're trying to run `app.js` with Node.js
- **Solution:** Don't run it with Node.js. Open the HTML file in a browser or use the Flask server

### CORS Errors
- Make sure `flask-cors` is installed: `pip install flask-cors`
- Check that CORS is enabled in `api.py`

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment variables (create .env file)
# Add your GROQ_API_KEY

# 3. Start the server
python api.py

# 4. Open browser
# Go to http://127.0.0.1:5000
```

That's it! The Flask server handles everything.

