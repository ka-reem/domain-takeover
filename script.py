import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Import credentials from config file
try:
    from config import CREDENTIALS
    print("Using credentials from config file")
except ImportError:
    print("Config file not found. Please create one based on config.example.py")
    exit(1)

class WebsiteAutomation:
    def __init__(self, url, headless=False):
        """Initialize the automation with the target website URL."""
        self.url = url
        self.options = Options()
        if headless:
            self.options.add_argument("--headless")
        
        # Performance optimizations
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-infobars")
        self.options.page_load_strategy = 'eager'  # Don't wait for all resources
        
        # Initialize the WebDriver
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self.options
        )
        # Set page load timeout
        self.driver.set_page_load_timeout(15)
        # Set default script timeout
        self.driver.set_script_timeout(10)
        
    def start(self):
        """Start the browser and navigate to the website."""
        try:
            self.driver.get(self.url)
            print(f"Successfully navigated to {self.url}")
        except Exception as e:
            print(f"Failed to navigate to {self.url}: {e}")
            self.quit()
    
    def wait_for_element(self, by, value, timeout=5):  # Reduced default timeout
        """Wait for an element to be present on the page."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            print(f"Timed out waiting for element {value}")
            return None
    
    def click_element(self, by, value, timeout=10):
        """Click on an element."""
        element = self.wait_for_element(by, value, timeout)
        if element:
            try:
                element.click()
                print(f"Clicked element {value}")
                return True
            except Exception as e:
                print(f"Failed to click element {value}: {e}")
                return False
        return False
    
    def fill_form(self, field_dict):
        """Fill out form fields. Provide a dictionary with locator tuples and values.
        Example: {(By.ID, 'username'): 'myusername', (By.NAME, 'password'): 'mypassword'}
        """
        for locator, value in field_dict.items():
            try:
                field = self.wait_for_element(locator[0], locator[1])
                if field:
                    field.clear()
                    field.send_keys(value)
                    print(f"Filled field {locator[1]} with value")
            except Exception as e:
                print(f"Failed to fill field {locator[1]}: {e}")
    
    def navigate_to(self, url):
        """Navigate to a different URL."""
        try:
            self.driver.get(url)
            print(f"Navigated to {url}")
        except Exception as e:
            print(f"Failed to navigate to {url}: {e}")
    
    def take_screenshot(self, filename):
        """Take a screenshot of the current page."""
        try:
            self.driver.save_screenshot(filename)
            print(f"Screenshot saved as {filename}")
        except Exception as e:
            print(f"Failed to take screenshot: {e}")
    
    def quick_login(self, email, password):
        """Optimized method to quickly perform login."""
        try:
            # Quick fill email
            email_field = self.wait_for_element(By.ID, 'email')
            if email_field:
                email_field.clear()
                email_field.send_keys(email)
            
            # Quick fill password
            password_field = self.wait_for_element(By.ID, 'password')
            if password_field:
                password_field.clear()
                password_field.send_keys(password)
            
            # Find the exact sign-in button using the class from HTML
            sign_in_button = self.wait_for_element(
                By.XPATH, 
                "//button[contains(@class, 'bg-primary') and contains(text(), 'Sign in')]"
            )
            
            if sign_in_button:
                sign_in_button.click()
                print("Clicked Sign in button")
                return True
            
            return False
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def quit(self):
        """Close the browser and end the session."""
        if self.driver:
            self.driver.quit()
            print("Browser session ended")

# Clean example usage
if __name__ == "__main__":
    # Static URL - will use csv later
    target_url = "https://lovable.dev/projects/..."
    
    # Create bot instance and start
    bot = WebsiteAutomation(target_url)
    bot.start()
    
    # Login with credentials from config
    success = bot.quick_login(
        CREDENTIALS.get('email'),
        CREDENTIALS.get('password')
    )
    
    # Keep browser open briefly to see results, then close
    time.sleep(10)
    bot.quit()
