#!/usr/bin/env python3
"""
Screenshot Bot - Takes screenshots of Redash dashboards and sends to Slack
Requires: pip install selenium requests pillow
"""

import requests
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image

# Configuration
REDASH_URL = "https://your-redash-instance.com"
REDASH_EMAIL = "your-email@company.com"
REDASH_PASSWORD = "your-password"
SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

def setup_driver():
    """Setup headless Chrome driver"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    return webdriver.Chrome(options=options)

def login_to_redash(driver):
    """Login to Redash"""
    driver.get(f"{REDASH_URL}/login")
    time.sleep(2)
    
    # Fill login form
    driver.find_element("name", "email").send_keys(REDASH_EMAIL)
    driver.find_element("name", "password").send_keys(REDASH_PASSWORD)
    driver.find_element("css selector", "button[type='submit']").click()
    
    time.sleep(3)

def screenshot_dashboard(driver, dashboard_id, name):
    """Take screenshot of dashboard and send to Slack"""
    url = f"{REDASH_URL}/dashboard/{dashboard_id}"
    driver.get(url)
    time.sleep(5)  # Wait for dashboard to load
    
    # Take screenshot
    screenshot_path = f"dashboard_{dashboard_id}.png"
    driver.save_screenshot(screenshot_path)
    
    # Send to Slack
    with open(screenshot_path, 'rb') as f:
        files = {'file': f}
        data = {
            'channels': '#your-channel',
            'initial_comment': f'📊 {name} Dashboard Screenshot',
            'token': 'xoxb-your-bot-token'  # Need bot token for file uploads
        }
        
        response = requests.post('https://slack.com/api/files.upload', files=files, data=data)
    
    # Clean up
    os.remove(screenshot_path)
    
    return response.status_code == 200

def main():
    """Main function"""
    dashboards = [
        {"id": 1, "name": "Sales Dashboard"},
        {"id": 2, "name": "User Analytics"},
        # Add your dashboards here
    ]
    
    driver = setup_driver()
    
    try:
        login_to_redash(driver)
        
        for dashboard in dashboards:
            print(f"Screenshotting: {dashboard['name']}")
            if screenshot_dashboard(driver, dashboard['id'], dashboard['name']):
                print(f"✅ Sent {dashboard['name']} to Slack")
            else:
                print(f"❌ Failed to send {dashboard['name']}")
            
            time.sleep(2)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()