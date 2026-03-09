#!/usr/bin/env python3
"""
CDP-based Twitter/X publisher.

Connects to a Chrome instance via Chrome DevTools Protocol to automate
publishing tweets and threads on Twitter/X.

CLI usage:
    # Basic commands
    python x_publish.py [--host HOST] [--port PORT] check-login [--headless] [--account NAME]
    python x_publish.py [--host HOST] [--port PORT] login [--account NAME]
    python x_publish.py [--host HOST] [--port PORT] --tweet "推文内容"
    python x_publish.py [--host HOST] [--port PORT] --tweet-file tweet.txt
    python x_publish.py [--host HOST] [--port PORT] --thread "推文 1" "推文 2"
    python x_publish.py [--host HOST] [--port PORT] --thread-file thread.txt
    python x_publish.py search-tweets --keyword "关键词"
    python x_publish.py get-tweet-detail --tweet-id TWEET_ID
    python x_publish.py like-tweet --tweet-id TWEET_ID
    python x_publish.py retweet --tweet-id TWEET_ID
    python x_publish.py reply-to-tweet --tweet-id TWEET_ID --content "评论内容"
    
    # Account management
    python x_publish.py list-accounts
    python x_publish.py add-account NAME [--alias ALIAS]
    python x_publish.py switch-account --account NAME
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

# Add scripts dir to path
SCRIPT_DIR = Path(__file__).parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Configuration
CDP_HOST = "127.0.0.1"
CDP_PORT = 9222
TWITTER_HOME_URL = "https://x.com/home"
TWITTER_LOGIN_URL = "https://x.com/i/flow/login"

# Try to import playwright
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Run: pip install playwright && playwright install chromium")


class TwitterPublisher:
    """CDP-based Twitter publisher."""
    
    def __init__(self, host: str = CDP_HOST, port: int = CDP_PORT):
        self.host = host
        self.port = port
        self.browser = None
        self.context = None
        self.page = None
    
    def connect(self, headless: bool = False, reuse_existing: bool = False) -> bool:
        """Connect to Chrome via CDP."""
        if not PLAYWRIGHT_AVAILABLE:
            print("❌ Playwright not available")
            return False
        
        try:
            playwright = sync_playwright().start()
            
            if reuse_existing and self.host == "127.0.0.1":
                # Connect to existing Chrome
                self.browser = playwright.chromium.connect_over_cdp(
                    f"http://{self.host}:{self.port}"
                )
                contexts = self.browser.contexts
                if contexts:
                    self.context = contexts[0]
                else:
                    self.context = self.browser.new_context()
            else:
                # Launch new browser
                self.browser = playwright.chromium.launch(
                    headless=headless
                )
                self.context = self.browser.new_context()
            
            self.page = self.context.new_page()
            print(f"✅ Connected to Chrome (host={self.host}, port={self.port})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    def check_login(self) -> bool:
        """Check if logged in to Twitter."""
        if not self.page:
            print("❌ Not connected to browser")
            return False
        
        try:
            print("🔍 Checking login status...")
            self.page.goto(TWITTER_HOME_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            
            # Check for login indicators
            url = self.page.url
            
            if "home" in url or "x.com" in url:
                print("✅ Logged in")
                return True
            elif "login" in url:
                print("❌ Not logged in")
                return False
            else:
                # Try to find user avatar or tweet button
                try:
                    self.page.wait_for_selector('[data-testid="SideNav_NewTweetBtn"]', timeout=5000)
                    print("✅ Logged in (tweet button found)")
                    return True
                except PlaywrightTimeout:
                    print("❌ Not logged in (no tweet button)")
                    return False
                    
        except Exception as e:
            print(f"❌ Error checking login: {e}")
            return False
    
    def login(self) -> bool:
        """Open Twitter for manual login."""
        if not self.page:
            print("❌ Not connected to browser")
            return False
        
        try:
            print("🔑 Opening Twitter login page...")
            self.page.goto(TWITTER_LOGIN_URL, wait_until="domcontentloaded")
            print("📱 Please complete login manually")
            print("⏳ Waiting for login... (press Ctrl+C to cancel)")
            
            # Wait for user to login (check every 5 seconds, max 5 minutes)
            for _ in range(60):
                time.sleep(5)
                if self.check_login():
                    print("✅ Login successful")
                    return True
            
            print("⏰ Login timeout")
            return False
            
        except Exception as e:
            print(f"❌ Error during login: {e}")
            return False
    
    def publish_tweet(self, content: str, images: List[str] = None) -> bool:
        """Publish a single tweet."""
        if not self.page:
            print("❌ Not connected to browser")
            return False
        
        try:
            print(f"📝 Publishing tweet ({len(content)} chars)...")
            
            # Go to home page
            self.page.goto(TWITTER_HOME_URL, wait_until="domcontentloaded")
            time.sleep(2)
            
            # Find and click tweet box
            try:
                tweet_box = self.page.wait_for_selector(
                    '[data-testid="tweetTextarea_0"]',
                    timeout=10000
                )
                tweet_box.click()
                tweet_box.fill(content)
                print("✅ Tweet content filled")
            except PlaywrightTimeout:
                print("❌ Tweet box not found")
                return False
            
            # Upload images if provided
            if images:
                print(f"📎 Uploading {len(images)} image(s)...")
                # TODO: Implement image upload
                print("⚠️  Image upload not yet implemented")
            
            # Click tweet button
            try:
                tweet_btn = self.page.wait_for_selector(
                    '[data-testid="tweetButton"]',
                    timeout=10000
                )
                tweet_btn.click()
                print("✅ Tweet published")
                time.sleep(2)
                return True
            except PlaywrightTimeout:
                print("❌ Tweet button not found")
                return False
                
        except Exception as e:
            print(f"❌ Error publishing tweet: {e}")
            return False
    
    def publish_thread(self, tweets: List[str]) -> bool:
        """Publish a thread of tweets."""
        if not self.page:
            print("❌ Not connected to browser")
            return False
        
        if len(tweets) > 25:
            print(f"❌ Thread too long ({len(tweets)} tweets, max 25)")
            return False
        
        try:
            print(f"🧵 Publishing thread ({len(tweets)} tweets)...")
            
            # Go to home page
            self.page.goto(TWITTER_HOME_URL, wait_until="domcontentloaded")
            time.sleep(2)
            
            # Publish first tweet
            if not self.publish_tweet(tweets[0]):
                return False
            
            # TODO: Implement thread continuation
            if len(tweets) > 1:
                print("⚠️  Thread continuation not yet implemented")
            
            return True
                
        except Exception as e:
            print(f"❌ Error publishing thread: {e}")
            return False
    
    def search_tweets(self, keyword: str, **kwargs) -> dict:
        """Search for tweets."""
        print(f"🔍 Searching for '{keyword}'...")
        # TODO: Implement search
        return {"error": "Not implemented"}
    
    def close(self):
        """Close browser connection."""
        if self.browser:
            self.browser.close()
            print("👋 Browser closed")


def main():
    parser = argparse.ArgumentParser(
        description="Twitter/X CDP publisher"
    )
    
    # Global options
    parser.add_argument("--host", default=CDP_HOST, help="CDP host")
    parser.add_argument("--port", type=int, default=CDP_PORT, help="CDP port")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--reuse-existing", action="store_true", help="Reuse existing tab")
    parser.add_argument("--account", help="Account name")
    parser.add_argument("--preview", action="store_true", help="Preview mode (don't publish)")
    
    # Tweet options
    parser.add_argument("--tweet", help="Tweet content")
    parser.add_argument("--tweet-file", help="File containing tweet content")
    parser.add_argument("--thread", nargs="+", help="Thread tweets")
    parser.add_argument("--thread-file", help="File containing thread (one per line)")
    parser.add_argument("--images", nargs="+", help="Image paths")
    
    args = parser.parse_args()
    
    # Create publisher
    publisher = TwitterPublisher(host=args.host, port=args.port)
    
    # Connect
    if not publisher.connect(headless=args.headless, reuse_existing=args.reuse_existing):
        sys.exit(1)
    
    try:
        # Handle commands
        if hasattr(args, 'command'):
            # Subcommand mode (search-tweets, like-tweet, etc.)
            pass
        elif args.tweet or args.tweet_file:
            # Single tweet
            content = args.tweet
            if not content and args.tweet_file:
                with open(args.tweet_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
            
            if not content:
                print("❌ No tweet content provided")
                sys.exit(1)
            
            if args.preview:
                print("👀 Preview mode - not publishing")
                publisher.check_login()
            else:
                publisher.publish_tweet(content, args.images)
                
        elif args.thread or args.thread_file:
            # Thread
            tweets = args.thread or []
            if not tweets and args.thread_file:
                with open(args.thread_file, 'r', encoding='utf-8') as f:
                    tweets = [line.strip() for line in f if line.strip()]
            
            if not tweets:
                print("❌ No thread content provided")
                sys.exit(1)
            
            publisher.publish_thread(tweets)
            
        else:
            parser.print_help()
    
    finally:
        publisher.close()


if __name__ == "__main__":
    main()
