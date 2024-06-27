import praw
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO
import logging
import time
import os

# Configure logging
logging.basicConfig(level=logging.INFO)

# Reddit API credentials
REDDIT_CLIENT_ID = 'YOUR_CLIENT_ID'
REDDIT_SECRET = 'YOUR_SECRET'
REDDIT_USER_AGENT = 'YOUR_USER_AGENT'
REDDIT_USERNAME = 'YOUR_USERNAME'
REDDIT_PASSWORD = 'YOUR_PASSWORD'

# Initialize Reddit API client
reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                     client_secret=REDDIT_SECRET,
                     user_agent=REDDIT_USER_AGENT,
                     username=REDDIT_USERNAME,
                     password=REDDIT_PASSWORD)


def get_post_image(subreddit, post_id, media_type):
    files_in_directory = os.listdir('title_pics')
    if any(f'{post_id}_title.png' in filename for filename in files_in_directory):
        return f'title_pics/{post_id}_title.png'  # Skip if the screenshot already exists
    logging.info(f"Fetching post with ID: {post_id}")
    post = reddit.submission(id=post_id)
    logging.info(f"Post URL: {post.url}")
    print(f"Post URL: {post.url}")  # Print the post URL
    with open('post_url.txt', 'w') as file:  # Save the post URL to a file
        file.write(post.url)
    
    if post.url.endswith(('.jpg', '.png', '.gif')):
        response = requests.get(post.url, headers={'User-Agent': REDDIT_USER_AGENT})
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            original_path = f'title_pics/{post_id}_original.png'
            img.save(original_path)
            print(f"Image saved at {original_path}")
            return original_path
        else:
            logging.error(f"Error fetching image: {response.status_code}")
            return None
    else:
        return take_screenshot_of_post(post, media_type)

def read_and_update_post_index(max_index):
    counter_file = 'post_index.txt'
    
    if not os.path.exists(counter_file):
        with open(counter_file, 'w') as f:
            f.write('0')

    with open(counter_file, 'r+') as f:
        index = int(f.read().strip())
        next_index = (index + 1) % max_index  # Increment and cycle back
        f.seek(0)
        f.write(str(next_index))
        f.truncate()

    return index

def take_screenshot_of_post(post, media_type):
    files_in_directory = os.listdir('title_pics')
    if any(f'{post.id}_title.png' in filename for filename in files_in_directory):
        return f'title_pics/{post.id}_title.png'  # Skip if the screenshot already exists

    options = Options()
    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    
    # Log in to Reddit
    login_url = 'https://www.reddit.com/login/'
    driver.get(login_url)
    
    # Wait for the login page to load and for the elements to be present
    wait = WebDriverWait(driver, 30)
    print("Trying to take screenshot")
    
    try:
        # Wait for the login to complete
        wait.until(EC.url_contains("https://www.reddit.com/"))
        print("login complete")
        
        # Navigate to the post URL
        driver.get(post.url)
        
        # Wait for the page to fully load
        time.sleep(5)

        # Locate the title element
        title_element = driver.find_element(By.CSS_SELECTOR, 'h1')  # Adjust the selector as needed
        location = title_element.location
        size = title_element.size

        # Adjust the coordinates for cropping
        left = location['x']
        top = location['y']
        right = left + 1000
        bottom = top + (size['height'] * 4)

        # Take a screenshot
        screenshot = driver.get_screenshot_as_png()
        driver.quit()

        img = Image.open(BytesIO(screenshot))

        # Crop the image
        img_cropped = img.crop((left, top, right, bottom))
        original_path = f'title_pics/{post.id}_original.png'
        img_cropped.save(original_path)

        print(f"Cropped screenshot saved at {original_path}")
        return original_path
    
    except Exception as e:
        logging.error(f"Error taking screenshot of post: {e}")
        driver.quit()
        return None


def getContent(subreddit, num_videos, text, num_comments):
    reddit_read_only = praw.Reddit(client_id="YOUR_CLIENT_ID",  # your client id
                                   client_secret="YOUR_CLIENT_SECRET",  # your client secret
                                   user_agent="YOUR_USER_AGENT",
                                   username=REDDIT_USERNAME,
                                   password=REDDIT_PASSWORD)  # your user agent

    subreddit = reddit_read_only.subreddit(subreddit)

    titles = []
    contents = []
    post_ids = []

    # Get the current post index
    post_index = read_and_update_post_index(5)  # Cycle through the first 5 posts
    
    if text == "comment":
        for idx, post in enumerate(subreddit.hot(limit=num_videos + post_index)):
            if idx < post_index: # or post.over_18:
                continue
            titles.append(post.title)
            post_ids.append(post.id)
            post.comments.replace_more(limit=0)  # Remove "load more comments"
            top_comments = post.comments.list()[:num_comments]
            contents.append([comment.body for comment in top_comments])
            if len(titles) >= num_videos:
                break
    elif text == "body":
        for idx, post in enumerate(subreddit.hot(limit=num_videos + post_index)):
            if idx < post_index: # or post.over_18:
                continue
            titles.append(post.title)
            contents.append(post.selftext)
            post_ids.append(post.id)
            if len(titles) >= num_videos:
                break
    else:
        print("Invalid text type, please enter either comment or body")
        exit(1)
    return titles, contents, post_ids

def byte_to_char_offset(text, byte_offset):
    encoded_text = text.encode('utf-8')
    byte_slice = encoded_text[:byte_offset]
    return len(byte_slice.decode('utf-8', errors='ignore'))

if __name__ == "__main__":
    main()
