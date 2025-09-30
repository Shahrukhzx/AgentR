from Browser.webrover_browser import WebRoverBrowser
from typing import Dict, Any, Tuple
from playwright.async_api import Page, Browser
import asyncio

async def setup_browser(go_to_page: str) -> Tuple[Browser, Page]:
    """
    Sets up a browser instance and returns the browser and page objects.
    """
    print(f"Setting up browser for {go_to_page}")
    
    try:
        browser = WebRoverBrowser()
        browser_obj, context = await browser.connect_to_chrome()

        page = await context.new_page()
        
        # Set longer timeout and better error handling
        try:
            print(f"Navigating to {go_to_page}...")
            await page.goto(go_to_page, timeout=60000, wait_until="domcontentloaded")
            print(f"Successfully loaded {go_to_page}")
        except Exception as e:
            print(f"Error loading page {go_to_page}: {e}")
            # Fallback to Google if the original page fails to load
            print("Falling back to Google...")
            try:
                await page.goto("https://www.google.com", timeout=60000, wait_until="domcontentloaded")
                print("Successfully loaded Google as fallback")
            except Exception as fallback_error:
                print(f"Even fallback failed: {fallback_error}")
                raise RuntimeError(f"Failed to load both target page and fallback: {fallback_error}")

        return browser, page
        
    except Exception as e:
        print(f"Failed to setup browser: {e}")
        # Make sure to cleanup on failure
        try:
            if 'browser' in locals():
                await browser.close()
        except:
            pass
        raise RuntimeError(f"Browser setup failed: {str(e)}")

async def cleanup_browser_session(browser: WebRoverBrowser) -> None:
    """
    Cleans up browser session using WebRoverBrowser's close method.
    This ensures proper cleanup of all resources including context, browser, and playwright.
    """
    try:
        if browser:
            print("Starting browser cleanup...")
            await browser.close()
            print("Browser session cleaned up successfully")
    except Exception as e:
        print(f"Error during browser cleanup: {e}")
        # Don't raise the exception, just log it
        # We want cleanup to be as robust as possible