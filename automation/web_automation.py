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

class WebsiteAutomation:
    """Core automation class for web interactions."""
    
    def __init__(self, url, headless=False, position_right=True):
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
        
        # Set window size and position
        # Modified browser window size - taller and narrower
        width = 1024  # Narrower width (reduced from 1200)
        height = 1300  # Taller height (increased from 800)
        
        # Position to the right side of the screen if requested
        if position_right:
            # Get screen resolution (approximate common screen width)
            screen_width = 3024  
            x_position = int(screen_width * 1/4)
            y_position = 0  # Top of the screen
            
            # Set window position and size
            self.driver.set_window_size(width, height)
            self.driver.set_window_position(x_position, y_position)
            print(f"Positioned browser window on right side of screen ({width}x{height})")
        else:
            # Still apply the size change when positioned on the left
            self.driver.set_window_size(width, height)
            print(f"Set browser window size to {width}x{height}")
        
        # Set page load timeout
        self.driver.set_page_load_timeout(15)
        # Set default script timeout
        self.driver.set_script_timeout(10)
    
    # Core navigation methods
    def start(self):
        """Start the browser and navigate to the website."""
        try:
            self.driver.get(self.url)
            print(f"Successfully navigated to {self.url}")
        except Exception as e:
            print(f"Failed to navigate to {self.url}: {e}")
            self.quit()
    
    def navigate_to(self, url):
        """Navigate to a different URL."""
        try:
            self.driver.get(url)
            print(f"Navigated to {url}")
        except Exception as e:
            print(f"Failed to navigate to {url}: {e}")
    
    def quit(self):
        """Close the browser and end the session."""
        if self.driver:
            self.driver.quit()
            print("Browser session ended")
    
    # Element interaction methods
    def wait_for_element(self, by, value, timeout=5):
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
        """Fill out form fields."""
        for locator, value in field_dict.items():
            try:
                field = self.wait_for_element(locator[0], locator[1])
                if field:
                    field.clear()
                    field.send_keys(value)
                    print(f"Filled field {locator[1]} with value")
            except Exception as e:
                print(f"Failed to fill field {locator[1]}: {e}")
    
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
    
    def save_element_text_to_file(self, by, value, filename, timeout=10):
        """Extract text from an element and save it to a file."""
        try:
            element = self.wait_for_element(by, value, timeout)
            if not element:
                print(f"Element {value} not found")
                return False
                
            text_content = element.text
            
            # Create directory if it doesn't exist
            directory = os.path.dirname(filename)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            # Write content to file
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(text_content)
                
            print(f"Successfully saved element text to {filename}")
            return True
        except Exception as e:
            print(f"Failed to save element text: {e}")
            return False
            
    def extract_chat_message(self, filename):
        """
        Extract the first chat message using method3 (using specific CSS path).
        
        Args:
            filename: The file to save the first chat message to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Using the CSS path that worked best
            css_selector = "body > div.flex.min-h-0.flex-1.flex-col > div > div.flex.min-h-0.flex-1.flex-col.bg-background > main > div > div > div.relative.inset-y-0.z-40.mr-0.flex.h-full.min-h-0.overflow-x-hidden.bg-background"
            
            # Find the chat container
            chat_container = self.driver.find_element(By.CSS_SELECTOR, css_selector)
            
            if not chat_container:
                print("Chat container not found using the provided CSS path")
                return False
            
            # Looking for divs with style containing "position: absolute; visibility: visible"
            visible_elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@style, 'position: absolute') and contains(@style, 'visibility: visible')]"
            )
            
            if not visible_elements:
                print("No visible message elements found")
                return False
            
            # Get the first visible element that contains a message
            for element in visible_elements:
                # Check if this element contains a message container
                message_containers = element.find_elements(By.CSS_SELECTOR, ".ChatMessageContainer")
                if message_containers:
                    text_content = message_containers[0].text
                    
                    # Create directory if it doesn't exist
                    directory = os.path.dirname(filename)
                    if directory and not os.path.exists(directory):
                        os.makedirs(directory)
                    
                    # Write content to file
                    with open(filename, 'w', encoding='utf-8') as file:
                        file.write(text_content)
                    
                    print(f"Successfully saved chat message to {filename}")
                    return True
            
            print("No message containers found within visible elements")
            return False
            
        except Exception as e:
            print(f"Error extracting chat message: {e}")
            return False
