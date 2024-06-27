from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import undetected_chromedriver as uc
import os
import pickle
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')

# TikTok credentials
TIKTOK_USERNAME = 'YOUR_USERNAME'
TIKTOK_PASSWORD = 'YOUR_PASSWORD'

def save_cookies(driver, filename):
    with open(filename, 'wb') as filehandler:
        pickle.dump(driver.get_cookies(), filehandler)

def load_cookies(driver, filename, domain):
    try:
        with open(filename, 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                if 'domain' in cookie:
                    cookie['domain'] = domain
                driver.add_cookie(cookie)
        logging.info(f"Loaded cookies from {filename}")
    except Exception as e:
        logging.error(f"Failed to load cookies: {e}")

def login_tiktok(driver):
    try:
        driver.get('https://www.tiktok.com/login/phone-or-email/email')
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Email or username']"))
        )
        
        # Enter the username and password
        username_input = driver.find_element(By.XPATH, "//input[@placeholder='Email or username']")
        password_input = driver.find_element(By.XPATH, "//input[@placeholder='Password']")
        
        username_input.send_keys(TIKTOK_USERNAME)
        password_input.send_keys(TIKTOK_PASSWORD)
        
        # Click the login button
        login_button = driver.find_element(By.XPATH, "//button[contains(text(),'Log in')]")
        login_button.click()
        time.sleep(5)  # Adjust the sleep time if necessary for login to complete

        # Wait for manual CAPTCHA solving
        logging.info("Please solve the CAPTCHA manually and press Enter to continue...")
        input("Please solve the CAPTCHA manually and press Enter to continue...")

        save_cookies(driver, "tiktok_cookies.pkl")
    except Exception as e:
        logging.error(f"An error occurred during login: {e}")
        driver.quit()
        raise

def post_to_tiktok(video_path, title, description):
    options = uc.ChromeOptions()
    options.binary_location = 'C:/Program Files/Google/Chrome/Application/chrome.exe'  # Updated path to the Chrome binary
    driver = uc.Chrome(options=options)
    try:
        # Load TikTok cookies if they exist
        if os.path.exists("tiktok_cookies.pkl"):
            driver.get('https://www.tiktok.com')
            load_cookies(driver, "tiktok_cookies.pkl", ".tiktok.com")
            driver.refresh()

        if not os.path.exists("tiktok_cookies.pkl"):
            login_tiktok(driver)
        
        logging.info("Navigating to upload page...")
        driver.get('https://www.tiktok.com/tiktokstudio/upload')
        
        logging.info("Waiting for the Select video button...")
        select_video_button = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'TUXButton-content') and contains(., 'Select videos')]"))
        )
        
        logging.info("Clicking the Select video button...")
        select_video_button.click()
        
        time.sleep(5)  # Adjust the sleep time if necessary
        
        logging.info("Uploading video...")
        upload_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        upload_input.send_keys(os.path.abspath(video_path))
        time.sleep(10)  # Allow time for the file to be processed

        # Add caption
        logging.info("Adding caption...")
        caption_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//textarea[@placeholder='Add a caption']"))
        )
        caption_area.send_keys(f"{title}\n{description}")
        
        logging.info("Clicking the Post button...")
        post_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Post')]"))
        )
        post_button.click()
        
        time.sleep(10)  # Adjust the sleep time if necessary
        logging.info("Post completed.")
        
    except Exception as e:
        logging.error(f"An error occurred during the posting process: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    try:
        # Verify that video file exists
        video_path = 'final_video_1.mp4'  # Update this with the actual video file path
        if not os.path.exists(video_path):
            logging.error("Video file does not exist.")
            raise FileNotFoundError("Video file does not exist.")
        
        # Example title and description
        title = "Check out this amazing video! #TikTok #Video"
        description = "This is a cool video I made. Don't forget to like and share! #CoolContent #FYP"

        post_to_tiktok(video_path, title, description)
    except Exception as e:
        logging.error(f"An error occurred in the main process: {e}")
