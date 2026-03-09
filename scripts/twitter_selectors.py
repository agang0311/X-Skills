"""
Twitter/X selectors - updated for 2026
"""

# Tweet textarea selectors (multiple attempts)
TWEET_TEXTAREA_SELECTORS = [
    '[data-testid="tweetTextarea_0"]',
    '[data-testid="tweetTextarea_1"]',
    'div[contenteditable="true"][role="textbox"]',
    'textarea[aria-label="Tweet text"]',
    'textarea[placeholder*="What is happening"]',
    'textarea[placeholder*="发生什么"]',
]

# Tweet button selectors (multiple attempts)
TWEET_BUTTON_SELECTORS = [
    '[data-testid="tweetButton"]',
    '[data-testid="tweetButtonInline"]',
    'button[aria-label="Post"]',
    'button[aria-label="发布"]',
    'div[role="button"]:has-text("发布")',
    'div[role="button"]:has-text("Post")',
]

# Image upload selectors
IMAGE_UPLOAD_SELECTORS = [
    '[data-testid="toolBarImages"]',
    '[aria-label="Media"]',
    'button[aria-label*="media"]',
    'button[aria-label*="图片"]',
]

# Add another post button (for threads)
ADD_POST_SELECTORS = [
    '[data-testid="addButton"]',
    'button:has-text("Add another post")',
    'button:has-text("添加另一篇帖子")',
]

def get_selector(selectors: list) -> str:
    """Return first selector from list."""
    return selectors[0] if selectors else None
