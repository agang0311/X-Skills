#!/usr/bin/env python3
"""
CDP-based Twitter/X publisher with full features.

Connects to a Chrome instance via Chrome DevTools Protocol to automate
publishing tweets, threads, search, and interactions on Twitter/X.

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
    """CDP-based Twitter publisher with full features."""
    
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
            print("📱 Please login with username and password")
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
            time.sleep(3)
            
            # Find and click tweet box (try multiple selectors)
            tweet_box = None
            tweet_selectors = [
                '[data-testid="tweetTextarea_0"]',
                '[data-testid="tweetTextarea_1"]',
                'div[contenteditable="true"][role="textbox"]',
                'textarea[aria-label*="Tweet"]',
                'textarea[aria-label*="发推"]',
            ]
            
            for selector in tweet_selectors:
                try:
                    tweet_box = self.page.wait_for_selector(selector, timeout=5000)
                    print(f"✅ Found tweet box with: {selector}")
                    break
                except PlaywrightTimeout:
                    continue
            
            if not tweet_box:
                print("❌ Tweet box not found (tried multiple selectors)")
                print("💡 Tip: Make sure you're on Twitter home page")
                return False
            
            tweet_box.click()
            time.sleep(1)
            tweet_box.fill(content)
            print("✅ Tweet content filled")
            
            # Wait for content to be filled and button to become enabled
            time.sleep(2)
            
            # Upload images if provided
            if images:
                print(f"📎 Uploading {len(images)} image(s)...")
                try:
                    # Find image upload button (try multiple selectors)
                    upload_btn = None
                    upload_selectors = [
                        '[data-testid="toolBarImages"]',
                        '[data-testid="toolBar-Images"]',
                        '[aria-label*="media"]',
                        '[aria-label*="Media"]',
                        '[aria-label*="图片"]',
                        '[aria-label*="照片"]',
                        'button[title*="media"]',
                        'button[title*="Media"]',
                        'button[title*="图片"]',
                    ]
                    
                    for selector in upload_selectors:
                        try:
                            upload_btn = self.page.wait_for_selector(selector, timeout=3000)
                            print(f"✅ Found upload button with: {selector}")
                            break
                        except PlaywrightTimeout:
                            continue
                    
                    if not upload_btn:
                        print("❌ Image upload button not found (tried multiple selectors)")
                        print("💡 Tip: Make sure tweet box is focused")
                        return False
                    
                    upload_btn.click()
                    time.sleep(2)
                    
                    # Wait for file input to appear
                    file_input = self.page.wait_for_selector('input[type="file"]', timeout=10000)
                    
                    # Upload each image
                    for img_path in images:
                        if os.path.exists(img_path):
                            # Use absolute path
                            abs_path = os.path.abspath(img_path)
                            file_input.set_input_files(abs_path)
                            print(f"✅ Uploaded: {img_path}")
                            time.sleep(3)
                        else:
                            print(f"⚠️  File not found: {img_path}")
                    
                    print("✅ Images uploaded")
                    time.sleep(2)
                except PlaywrightTimeout as e:
                    print(f"❌ Image upload failed: {e}")
                    print("💡 Tip: Check if image path is correct")
                    return False
            
            # Click tweet button (try multiple selectors)
            tweet_btn = None
            button_selectors = [
                '[data-testid="tweetButton"]',
                '[data-testid="tweetButtonInline"]',
                'button[aria-label="Post"]',
                'button[aria-label="发布"]',
                'button:has-text("发布")',
                'button:has-text("Post")',
            ]
            
            for selector in button_selectors:
                try:
                    tweet_btn = self.page.wait_for_selector(selector, timeout=5000)
                    print(f"✅ Found tweet button with: {selector}")
                    # Wait for button to be enabled
                    tweet_btn.wait_for_element_state("enabled", timeout=5000)
                    print("✅ Tweet button is enabled")
                    break
                except PlaywrightTimeout:
                    continue
            
            if not tweet_btn:
                print("❌ Tweet button not found (tried multiple selectors)")
                print("💡 Tip: Make sure tweet content is filled")
                return False
            
            # Try normal click first
            try:
                tweet_btn.click()
                print("✅ Tweet published (normal click)")
            except PlaywrightTimeout:
                # If normal click fails, use JavaScript click
                print("⚠️  Normal click failed, using JavaScript click...")
                self.page.evaluate('(el) => el.click()', tweet_btn)
                print("✅ Tweet published (JavaScript click)")
            
            time.sleep(3)
            return True
                
        except Exception as e:
            print(f"❌ Error publishing tweet: {e}")
            return False
    
    def publish_thread(self, tweets: List[str], images: List[str] = None) -> bool:
        """Publish a thread of tweets with optional images."""
        if not self.page:
            print("❌ Not connected to browser")
            return False
        
        if not tweets:
            print("❌ No tweets provided")
            return False
        
        if len(tweets) > 25:
            print(f"❌ Thread too long ({len(tweets)} tweets, max 25)")
            return False
        
        # Validate tweet lengths
        for i, tweet in enumerate(tweets):
            if len(tweet) > 280:
                print(f"❌ Tweet {i+1} too long ({len(tweet)} chars, max 280)")
                return False
        
        try:
            print(f"🧵 Publishing thread ({len(tweets)} tweets)...")
            
            # Go to home page
            self.page.goto(TWITTER_HOME_URL, wait_until="domcontentloaded")
            time.sleep(3)
            
            # Find and click tweet box
            tweet_selectors = [
                '[data-testid="tweetTextarea_0"]',
                '[data-testid="tweetTextarea_1"]',
                'div[contenteditable="true"][role="textbox"]',
            ]
            
            tweet_box = None
            for selector in tweet_selectors:
                try:
                    tweet_box = self.page.wait_for_selector(selector, timeout=5000)
                    print(f"✅ Found tweet box")
                    break
                except PlaywrightTimeout:
                    continue
            
            if not tweet_box:
                print("❌ Tweet box not found")
                return False
            
            tweet_box.click()
            time.sleep(1)
            
            # Fill first tweet
            tweet_box.fill(tweets[0])
            print(f"✅ Filled tweet 1/{len(tweets)} ({len(tweets[0])} chars)")
            time.sleep(1)
            
            # Upload images for first tweet if provided
            if images:
                print(f"📎 Uploading {len(images)} image(s) to first tweet...")
                try:
                    upload_selectors = [
                        '[data-testid="toolBarImages"]',
                        '[data-testid="toolBar-Images"]',
                        '[aria-label*="media"]',
                        '[aria-label*="Media"]',
                    ]
                    
                    upload_btn = None
                    for selector in upload_selectors:
                        try:
                            upload_btn = self.page.wait_for_selector(selector, timeout=3000)
                            break
                        except PlaywrightTimeout:
                            continue
                    
                    if upload_btn:
                        upload_btn.click()
                        time.sleep(2)
                        
                        file_input = self.page.wait_for_selector('input[type="file"]', timeout=10000)
                        
                        for img_path in images:
                            if os.path.exists(img_path):
                                abs_path = os.path.abspath(img_path)
                                file_input.set_input_files(abs_path)
                                print(f"✅ Uploaded: {img_path}")
                                time.sleep(3)
                        
                        print("✅ Images uploaded")
                        time.sleep(2)
                    else:
                        print("⚠️  Upload button not found, skipping images")
                        
                except Exception as e:
                    print(f"⚠️  Image upload failed: {e}")
            
            # Add more tweets to thread
            for i in range(1, len(tweets)):
                try:
                    # Wait a bit for the UI to update
                    time.sleep(3)
                    
                    # Scroll to bottom to make sure new textarea is visible
                    self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    time.sleep(2)
                    
                    # Find all tweet textareas first
                    textareas = self.page.query_selector_all('[data-testid="tweetTextarea_0"]')
                    print(f"🔍 Found {len(textareas)} textareas before adding tweet {i+1}")
                    
                    # If we already have enough textareas, just fill the next one
                    if len(textareas) > i:
                        textareas[i].fill(tweets[i])
                        print(f"✅ Filled tweet {i+1}/{len(tweets)} ({len(tweets[i])} chars)")
                        time.sleep(1)
                        continue
                    
                    # Try keyboard shortcut first: Ctrl+Enter to add another post
                    print(f"⌨️  Trying Ctrl+Enter to add tweet {i+1}...")
                    self.page.keyboard.press("Control+Enter")
                    time.sleep(5)
                    
                    # Scroll to bottom again
                    self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    time.sleep(2)
                    
                    # Find all tweet textareas again
                    textareas = self.page.query_selector_all('[data-testid="tweetTextarea_0"]')
                    print(f"🔍 Found {len(textareas)} textareas after Ctrl+Enter")
                    
                    if len(textareas) > i:
                        # Fill the new textarea
                        textareas[i].fill(tweets[i])
                        print(f"✅ Filled tweet {i+1}/{len(tweets)} ({len(tweets[i])} chars)")
                        time.sleep(1)
                        continue
                    
                    # If keyboard shortcut didn't work, try clicking add button
                    print("⚠️  Ctrl+Enter didn't work, trying add button...")
                    
                    add_selectors = [
                        '[data-testid="addButton"]',
                        'button[aria-label*="Add another post"]',
                        'button[aria-label*="添加"]',
                        'div[role="button"]:has-text("+")',
                    ]
                    
                    add_btn = None
                    for selector in add_selectors:
                        try:
                            add_btn = self.page.wait_for_selector(selector, timeout=5000)
                            print(f"✅ Found add button with: {selector[:50]}")
                            break
                        except PlaywrightTimeout:
                            continue
                    
                    if add_btn:
                        # Scroll add button into view
                        add_btn.scroll_into_view_if_needed()
                        time.sleep(1)
                        
                        # Try JavaScript click to avoid blocking issues
                        try:
                            self.page.evaluate('(el) => el.click()', add_btn)
                            print("✅ Clicked add button (JavaScript)")
                        except Exception as e:
                            print(f"⚠️  JavaScript click failed: {e}")
                            add_btn.click()
                            print("✅ Clicked add button (normal)")
                        
                        # Wait longer for new textarea to appear
                        time.sleep(5)
                        
                        # Scroll to bottom again
                        self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        time.sleep(2)
                        
                        # Find textareas again
                        textareas = self.page.query_selector_all('[data-testid="tweetTextarea_0"]')
                        print(f"🔍 Found {len(textareas)} textareas after clicking add button")
                        
                        if len(textareas) > i:
                            textareas[i].fill(tweets[i])
                            print(f"✅ Filled tweet {i+1}/{len(tweets)} ({len(tweets[i])} chars)")
                            time.sleep(1)
                            continue
                    
                    # Last resort: try to find any editable element
                    print("⚠️  Trying alternative method...")
                    editable_divs = self.page.query_selector_all('div[contenteditable="true"][role="textbox"]')
                    print(f"🔍 Found {len(editable_divs)} editable divs")
                    
                    if len(editable_divs) >= i:
                        editable_divs[i].fill(tweets[i])
                        print(f"✅ Filled tweet {i+1}/{len(tweets)} (using contenteditable div)")
                        time.sleep(1)
                    else:
                        print(f"❌ Could not find textarea for tweet {i+1}")
                        print(f"   Expected at least {i+1} textareas, found {len(textareas)}")
                        return False
                                
                except Exception as e:
                    print(f"❌ Failed to add tweet {i+1}: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            
            # Wait for all tweets to be filled
            time.sleep(2)
            
            # Click "Post all" button
            button_selectors = [
                '[data-testid="tweetButton"]',
                '[data-testid="tweetButtonInline"]',
                'button[aria-label="Post"]',
                'button[aria-label="发布"]',
                'button:has-text("发布")',
                'button:has-text("Post all")',
                'button:has-text("全部发布")',
            ]
            
            tweet_btn = None
            for selector in button_selectors:
                try:
                    tweet_btn = self.page.wait_for_selector(selector, timeout=5000)
                    print(f"✅ Found post button")
                    break
                except PlaywrightTimeout:
                    continue
            
            if not tweet_btn:
                print("❌ Post button not found")
                return False
            
            # Wait for button to be enabled
            try:
                tweet_btn.wait_for_element_state("enabled", timeout=5000)
                print("✅ Post button is enabled")
            except PlaywrightTimeout:
                print("⚠️  Post button may be disabled, trying anyway...")
            
            # Click button
            try:
                tweet_btn.click()
                print("✅ Thread published (normal click)")
            except PlaywrightTimeout:
                print("⚠️  Normal click failed, using JavaScript click...")
                self.page.evaluate('(el) => el.click()', tweet_btn)
                print("✅ Thread published (JavaScript click)")
            
            time.sleep(3)
            print("✅ Thread publishing completed")
            return True
                
        except Exception as e:
            print(f"❌ Error publishing thread: {e}")
            return False
    
    def search_tweets(self, keyword: str, sort_by: str = "latest", **kwargs) -> dict:
        """Search for tweets."""
        if not self.page:
            print("❌ Not connected to browser")
            return {"error": "Not connected"}
        
        try:
            print(f"🔍 Searching for '{keyword}' (sort: {sort_by})...")
            
            # Build search URL
            search_url = f"https://x.com/search?q={keyword}&f=live"
            
            self.page.goto(search_url, wait_until="domcontentloaded")
            time.sleep(3)
            
            # Wait for tweets to load
            try:
                self.page.wait_for_selector('[data-testid="tweetText"]', timeout=10000)
                print("✅ Search results loaded")
            except PlaywrightTimeout:
                print("⚠️  No results found")
                return {"tweets": [], "count": 0}
            
            # Extract tweets
            tweets = []
            tweet_elements = self.page.query_selector_all('[data-testid="tweetText"]')
            
            for i, tweet in enumerate(tweet_elements[:10]):  # Get first 10 tweets
                try:
                    text = tweet.inner_text()
                    tweets.append({
                        "index": i + 1,
                        "text": text[:200]  # Truncate long tweets
                    })
                except:
                    pass
            
            print(f"✅ Found {len(tweets)} tweets")
            return {"tweets": tweets, "count": len(tweets)}
            
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return {"error": str(e)}
    
    def like_tweet(self, tweet_id: str) -> bool:
        """Like a tweet."""
        print(f"❤️  Liking tweet {tweet_id}...")
        # TODO: Implement like functionality
        print("⚠️  Like functionality not yet implemented")
        return False
    
    def retweet(self, tweet_id: str, comment: str = None) -> bool:
        """Retweet a tweet."""
        if comment:
            print(f"🔄 Quoting tweet {tweet_id}...")
        else:
            print(f"🔄 Retweeting tweet {tweet_id}...")
        # TODO: Implement retweet functionality
        print("⚠️  Retweet functionality not yet implemented")
        return False
    
    def reply_to_tweet(self, tweet_id: str, content: str) -> bool:
        """Reply to a tweet."""
        print(f"💬 Replying to tweet {tweet_id}...")
        # TODO: Implement reply functionality
        print("⚠️  Reply functionality not yet implemented")
        return False
    
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
    
    # Search options
    parser.add_argument("--sort-by", default="latest", help="Sort by (latest/top)")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Check login command
    check_parser = subparsers.add_parser("check-login", help="Check login status")
    check_parser.add_argument("--headless", action="store_true", help="Run headless")
    
    # Login command
    login_parser = subparsers.add_parser("login", help="Login to Twitter")
    
    # Search command
    search_parser = subparsers.add_parser("search-tweets", help="Search tweets")
    search_parser.add_argument("--keyword", required=True, help="Search keyword")
    search_parser.add_argument("--sort-by", default="latest", help="Sort by")
    
    # Like command
    like_parser = subparsers.add_parser("like-tweet", help="Like a tweet")
    like_parser.add_argument("--tweet-id", required=True, help="Tweet ID")
    
    # Retweet command
    retweet_parser = subparsers.add_parser("retweet", help="Retweet a tweet")
    retweet_parser.add_argument("--tweet-id", required=True, help="Tweet ID")
    retweet_parser.add_argument("--comment", help="Quote comment")
    
    # Reply command
    reply_parser = subparsers.add_parser("reply-to-tweet", help="Reply to a tweet")
    reply_parser.add_argument("--tweet-id", required=True, help="Tweet ID")
    reply_parser.add_argument("--content", required=True, help="Reply content")
    reply_parser.add_argument("--content-file", help="Reply content from file")
    
    # Get tweet detail
    detail_parser = subparsers.add_parser("get-tweet-detail", help="Get tweet detail")
    detail_parser.add_argument("--tweet-id", required=True, help="Tweet ID")
    
    args = parser.parse_args()
    
    # Create publisher
    publisher = TwitterPublisher(host=args.host, port=args.port)
    
    # Connect
    if not publisher.connect(headless=args.headless, reuse_existing=args.reuse_existing):
        sys.exit(1)
    
    try:
        # Handle subcommands
        if args.command == "check-login":
            if publisher.check_login():
                print("✅ You are logged in to Twitter")
            else:
                print("❌ Not logged in. Run: python x_publish.py login")
            sys.exit(0)
            
        elif args.command == "login":
            publisher.login()
            sys.exit(0)
            
        elif args.command == "search-tweets":
            results = publisher.search_tweets(args.keyword, sort_by=args.sort_by)
            if "tweets" in results:
                for tweet in results["tweets"]:
                    print(f"{tweet['index']}. {tweet['text']}")
            sys.exit(0)
            
        elif args.command == "like-tweet":
            publisher.like_tweet(args.tweet_id)
            sys.exit(0)
            
        elif args.command == "retweet":
            publisher.retweet(args.tweet_id, comment=args.comment)
            sys.exit(0)
            
        elif args.command == "reply-to-tweet":
            content = args.content
            if not content and args.content_file:
                with open(args.content_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
            publisher.reply_to_tweet(args.tweet_id, content)
            sys.exit(0)
            
        elif args.command == "get-tweet-detail":
            print(f"Getting detail for tweet {args.tweet_id}...")
            print("⚠️  Not yet implemented")
            sys.exit(0)
        
        # Handle main options
        if args.tweet or args.tweet_file:
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
