import os
import asyncio
from flask import Flask, request, send_file, jsonify
from playwright.async_api import async_playwright
import io

app = Flask(__name__)

# Global variable for the browser instance
browser = None
playwright_instance = None

async def initialize_browser():
    """Initialize the browser instance."""
    global browser, playwright_instance
    if not browser:
        print("--- Initializing new browser instance ---")
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

@app.route("/", methods=["GET"])
def index():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Screenshot service is running."})

@app.route("/screenshot", methods=["POST"])
def take_screenshot():
    """Takes a screenshot of a given URL."""
    
    async def async_screenshot():
        global browser
        if not browser:
            await initialize_browser()

        data = request.get_json()
        if not data or "url" not in data:
            return None, "URL is required"

        url = data["url"]
        print(f"--- Taking screenshot of: {url} ---")

        page = None
        try:
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(url, wait_until='networkidle', timeout=30000)
            screenshot_bytes = await page.screenshot(type='png')
            return screenshot_bytes, None
        except Exception as e:
            print(f"Error: {str(e)}")
            return None, str(e)
        finally:
            if page:
                await page.close()

    # Run the async function
    screenshot_bytes, error = asyncio.run(async_screenshot())
    
    if error:
        return jsonify({"error": error}), 500
    
    return send_file(
        io.BytesIO(screenshot_bytes),
        mimetype='image/png',
        as_attachment=True,
        download_name='screenshot.png'
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
