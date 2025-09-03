import os
import asyncio
from flask import Flask, request, send_file, jsonify
from playwright.async_api import async_playwright
import io

app = Flask(__name__)

# Global variables to hold the single browser instance and a lock.
browser = None
playwright_instance = None
browser_lock = asyncio.Lock()

async def get_browser():
    """
    Initializes and returns a single, shared browser instance.
    Uses a lock to prevent race conditions.
    """
    global browser, playwright_instance
    async with browser_lock:
        if not browser or not browser.is_connected():
            print("--- Initializing new browser instance ---")
            if playwright_instance:
                await playwright_instance.stop()
            
            playwright_instance = await async_playwright().start()
            browser = await playwright_instance.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu'
                ]
            )
            print("--- Browser initialized successfully ---")
    return browser

@app.route("/", methods=["GET"])
def index():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Screenshot service is running."})

@app.route("/screenshot", methods=["POST"])
def take_screenshot_route():
    # This wrapper function is needed to run an async function from a sync Flask route.
    return asyncio.run(handle_screenshot_request())

async def handle_screenshot_request():
    """
    The actual async logic for taking a screenshot.
    """
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "URL is required"}), 400

    url = data["url"]
    print(f"--- Taking screenshot of: {url} ---")
    
    page = None
    try:
        b = await get_browser()
        page = await b.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        # Increased timeout for slow-loading pages
        await page.goto(url, wait_until='networkidle', timeout=60000) 
        
        screenshot_bytes = await page.screenshot(type='png')
        
        return send_file(
            io.BytesIO(screenshot_bytes),
            mimetype='image/png',
            as_attachment=True,
            download_name='screenshot.png'
        )
    except Exception as e:
        error_message = f"Failed to capture screenshot: {str(e)}"
        print(f"--- ERROR: {error_message} ---")
        return jsonify({"error": error_message}), 500
    finally:
        if page:
            await page.close()

# The __main__ block is only for local testing, Gunicorn will not use it.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
