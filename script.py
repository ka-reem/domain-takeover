import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class WebsiteAutomation:
    def __init__(self, url, headless=False):
        """Initialize the automation with the target website URL."""
        self.url = url
        self.options = Options()
        if headless:
            self.options.add_argument("--headless")
        
        # Add additional options for stability
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        
        # Initialize the WebDriver
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self.options
        )
        
    def start(self):
        """Start the browser and navigate to the website."""
        try:
            self.driver.get(self.url)
            print(f"Successfully navigated to {self.url}")
        except Exception as e:
            print(f"Failed to navigate to {self.url}: {e}")
            self.quit()
    
    def wait_for_element(self, by, value, timeout=10):
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
    
    def quit(self):
        """Close the browser and end the session."""
        if self.driver:
            self.driver.quit()
            print("Browser session ended")

# Example usage
if __name__ == "__main__":
    # Initialize the automation
    # bot = WebsiteAutomation("https://lovable.dev")
    # Should get the URL from csv file
    
    # Start the browser and navigate to the website
    bot.start()
    
    # Example: Wait for a while to see the page
    time.sleep(2)
    
    # Example: Fill out a login form
    # bot.fill_form({
    #     (By.ID, 'username'): 'your_username',
    #     (By.ID, 'password'): 'your_password'
    # })
    
    # Example: Click a button
    # bot.click_element(By.XPATH, "//button[contains(text(), 'Log In')]")
    
    # Example: Navigate to another page
    # bot.navigate_to("https://example.com/another-page")
    
    # Example: Take a screenshot
    # bot.take_screenshot("screenshot.png")
    
    # End the session after 10 seconds
    time.slee(10)
    bot.quit()
