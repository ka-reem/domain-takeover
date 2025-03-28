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
        
        # Enable browser logging
        self.options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        
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
        
        # Set page load timeout - reduced from 15 seconds
        self.driver.set_page_load_timeout(10)
        # Set default script timeout - reduced from 10 seconds
        self.driver.set_script_timeout(7)
    
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
        """
        Navigate to a different URL and ensure the navigation was successful.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        try:
            print(f"Navigating to {url}")
            self.driver.get(url)
            
            # Wait briefly - reduced from 2 seconds
            time.sleep(1.5)
            
            # Verify we reached the intended URL or at least the right domain
            current_url = self.driver.current_url
            
            if current_url == url:
                print(f"Successfully navigated to exact URL: {url}")
                return True
            elif url in current_url or (
                "lovable.dev/projects/" in url and "lovable.dev/projects/" in current_url
            ):
                print(f"Navigation partially successful. Landed on: {current_url}")
                return True
            else:
                print(f"Navigation may have been redirected. Current URL: {current_url}")
                
                # If we're on the homepage but wanted a specific project, try one more direct navigation
                if current_url == "https://lovable.dev/" and "projects" in url:
                    print("Detected redirection to homepage. Trying direct navigation again...")
                    self.driver.get(url)
                    time.sleep(3)
                    
                    if url in self.driver.current_url or "projects" in self.driver.current_url:
                        print(f"Second navigation attempt successful. Now at: {self.driver.current_url}")
                        return True
                
                return False
                
        except Exception as e:
            print(f"Failed to navigate to {url}: {e}")
            return False
    
    def get_current_url(self):
        """Get the current URL of the browser."""
        return self.driver.current_url
    
    def is_on_correct_page(self, expected_url):
        """Check if we're on the expected page or at least on a project page."""
        current_url = self.driver.current_url
        
        if current_url == expected_url:
            return True
        
        # Check if we're at least on a project page (useful for handling redirects)
        if "lovable.dev/projects/" in expected_url and "lovable.dev/projects/" in current_url:
            return True
            
        return False
    
    def quit(self):
        """Close the browser and end the session."""
        if self.driver:
            self.driver.quit()
            print("Browser session ended")
    
    # Element interaction methods
    def wait_for_element(self, by, value, timeout=3):  # Default timeout reduced from 5
        """Wait for an element to be present on the page."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            print(f"Timed out waiting for element {value}")
            return None
    
    def click_element(self, by, value, timeout=7):  # Default timeout reduced from 10
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
        Extract the first chat message using multiple methods as fallbacks.
        
        Args:
            filename: The file to save the first chat message to
            
        Returns:
            bool: True if successful, False otherwise
        """
        print("Attempting to extract chat message...")
        
        # Take a screenshot before attempting extraction (helpful for debugging)
        pre_extract_screenshot = os.path.splitext(filename)[0] + "_pre_extract.png"
        try:
            self.driver.save_screenshot(pre_extract_screenshot)
            print(f"Saved pre-extraction screenshot to {pre_extract_screenshot}")
        except Exception as e:
            print(f"Could not save pre-extraction screenshot: {e}")
        
        # Try multiple methods to find chat messages
        try:
            # Method 1: Look for ChatMessageContainer class directly (most reliable)
            print("Method 1: Looking for ChatMessageContainer elements...")
            message_containers = self.driver.find_elements(By.CSS_SELECTOR, ".ChatMessageContainer")
            
            if message_containers:
                print(f"Found {len(message_containers)} message containers")
                # Get the first container (oldest message)
                text_content = message_containers[0].text
                if text_content:
                    self._save_text_to_file(text_content, filename)
                    return True
            else:
                print("No ChatMessageContainer elements found")
                
            # Method 2: Look for any elements with data-message-id attribute
            print("Method 2: Looking for elements with data-message-id...")
            message_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-message-id]")
            
            if message_elements:
                print(f"Found {len(message_elements)} message elements with data-message-id")
                # Get the first one
                text_content = message_elements[0].text
                if text_content:
                    self._save_text_to_file(text_content, filename)
                    return True
            else:
                print("No elements with data-message-id found")
                
            # Method 3: Look for message content by class names often used in chat interfaces
            print("Method 3: Looking for message content by class names...")
            content_classes = [
                ".prose", ".prose-markdown", ".break-anywhere", ".whitespace-pre-wrap", 
                ".message-content", ".chat-message", ".user-message"
            ]
            
            for class_selector in content_classes:
                elements = self.driver.find_elements(By.CSS_SELECTOR, class_selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector {class_selector}")
                    text_content = elements[0].text
                    if text_content:
                        self._save_text_to_file(text_content, filename)
                        return True
            
            # Method 4: Last resort - take any visible text from the main area
            print("Method 4: Taking screenshot and looking for any visible text...")
            
            # Look for main content area using a more general selector
            main_areas = self.driver.find_elements(By.CSS_SELECTOR, "main")
            if main_areas:
                for main in main_areas:
                    try:
                        # Get all paragraph elements
                        paragraphs = main.find_elements(By.TAG_NAME, "p")
                        if paragraphs:
                            # Collect text from all paragraphs
                            all_text = "\n".join([p.text for p in paragraphs if p.text])
                            if all_text:
                                self._save_text_to_file(all_text, filename)
                                return True
                    except Exception as e:
                        print(f"Error extracting paragraphs: {e}")
            
            # Take a screenshot for debugging
            debug_screenshot = os.path.splitext(filename)[0] + "_debug.png"
            self.driver.save_screenshot(debug_screenshot)
            print(f"Saved debug screenshot to {debug_screenshot}")
            
            print("All extraction methods failed")
            return False
            
        except Exception as e:
            print(f"Error extracting chat message: {e}")
            # Take a screenshot for debugging
            try:
                debug_screenshot = os.path.splitext(filename)[0] + "_error.png"
                self.driver.save_screenshot(debug_screenshot)
                print(f"Saved error screenshot to {debug_screenshot}")
            except:
                pass
            return False
    
    def extract_chat_message_to_memory(self):
        """
        Extract the first chat message and return it as text rather than saving to file.
        
        Returns:
            str: Extracted text content or None if extraction failed
        """
        print("Attempting to extract chat message...")
        
        # Try multiple methods to find chat messages
        try:
            # Method 1: Look for ChatMessageContainer class directly (most reliable)
            print("Method 1: Looking for ChatMessageContainer elements...")
            message_containers = self.driver.find_elements(By.CSS_SELECTOR, ".ChatMessageContainer")
            
            if message_containers:
                print(f"Found {len(message_containers)} message containers")
                # Get the first container (oldest message)
                text_content = message_containers[0].text
                if text_content:
                    print(f"Successfully extracted chat message of {len(text_content)} characters")
                    return text_content
            else:
                print("No ChatMessageContainer elements found")
                
            # Method 2: Look for any elements with data-message-id attribute
            print("Method 2: Looking for elements with data-message-id...")
            message_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-message-id]")
            
            if message_elements:
                print(f"Found {len(message_elements)} message elements with data-message-id")
                # Get the first one
                text_content = message_elements[0].text
                if text_content:
                    print(f"Successfully extracted chat message of {len(text_content)} characters")
                    return text_content
            else:
                print("No elements with data-message-id found")
                
            # Method 3: Look for message content by class names often used in chat interfaces
            print("Method 3: Looking for message content by class names...")
            content_classes = [
                ".prose", ".prose-markdown", ".break-anywhere", ".whitespace-pre-wrap", 
                ".message-content", ".chat-message", ".user-message"
            ]
            
            for class_selector in content_classes:
                elements = self.driver.find_elements(By.CSS_SELECTOR, class_selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector {class_selector}")
                    text_content = elements[0].text
                    if text_content:
                        print(f"Successfully extracted chat message of {len(text_content)} characters")
                        return text_content
            
            # Method 4: Last resort - take any visible text from the main area
            print("Method 4: Looking for any visible text...")
            
            # Look for main content area using a more general selector
            main_areas = self.driver.find_elements(By.CSS_SELECTOR, "main")
            if main_areas:
                for main in main_areas:
                    try:
                        # Get all paragraph elements
                        paragraphs = main.find_elements(By.TAG_NAME, "p")
                        if paragraphs:
                            # Collect text from all paragraphs
                            all_text = "\n".join([p.text for p in paragraphs if p.text])
                            if all_text:
                                print(f"Successfully extracted {len(all_text)} characters from paragraphs")
                                return all_text
                    except Exception as e:
                        print(f"Error extracting paragraphs: {e}")
            
            # Save a debug screenshot without saving text
            debug_screenshot = os.path.join(os.getcwd(), "debug_screenshots", f"extract_failed_{int(time.time())}.png")
            os.makedirs(os.path.dirname(debug_screenshot), exist_ok=True)
            self.driver.save_screenshot(debug_screenshot)
            print(f"Saved debug screenshot to {debug_screenshot}")
            
            print("All extraction methods failed")
            return None
            
        except Exception as e:
            print(f"Error extracting chat message: {e}")
            return None
    
    def _save_text_to_file(self, text_content, filename):
        """
        Helper method to save text content to a file.
        
        Args:
            text_content: The text content to save
            filename: The file to save the text to
        """
        # Create directory if it doesn't exist
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Write content to file
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(text_content)
        
        print(f"Successfully saved text content to {filename}")
    
    def get_console_logs(self):
        """
        Get browser console logs.
        
        Returns:
            list: Console log entries
        """
        try:
            logs = self.driver.get_log('browser')
            return logs
        except Exception as e:
            print(f"Error getting console logs: {e}")
            return []
    
    def check_console_for_errors(self, keywords=None):
        """
        Check browser console logs for errors or specific keywords.
        
        Args:
            keywords: List of keywords to look for in console messages
            
        Returns:
            tuple: (has_errors, error_messages)
        """
        if keywords is None:
            keywords = ['error', 'exception', 'fail', 'already', 'taken', 'exists']
            
        logs = self.get_console_logs()
        error_messages = []
        
        for log in logs:
            log_level = log.get('level', '').lower()
            log_message = log.get('message', '').lower()
            
            # Check for error level or keywords in message
            if log_level == 'severe' or any(keyword.lower() in log_message for keyword in keywords):
                error_messages.append(log)
                
        has_errors = len(error_messages) > 0
        return has_errors, error_messages
    
    def extract_project_description(self, timeout=5):
        """
        Extract the project description from the page.
        
        Args:
            timeout: Maximum time to wait for description element
            
        Returns:
            str: Extracted description or empty string if not found
        """
        try:
            print("Attempting to extract project description...")
            
            # Try multiple selectors that might contain the description
            description_selectors = [
                "//div[contains(@class, 'prose')]/p",
                "//div[contains(@class, 'description')]/p",
                "//p[contains(@class, 'description')]",
                "//div[@role='dialog']//p",
                "//div[@data-radix-dialog-content]//p"
            ]
            
            for selector in description_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    # Get text from the first paragraph element
                    description = elements[0].text.strip()
                    if description:
                        print(f"Found description: '{description[:50]}...'")
                        return description
            
            print("Could not find project description")
            return ""
            
        except Exception as e:
            print(f"Error extracting project description: {e}")
            return ""
    
    def extract_custom_url(self, timeout=5):
        """
        Extract the custom URL in the format "(name).lovable.app" from the page.
        Priority is given to the format with SVG icon and potential "Not published" status.
        
        Args:
            timeout: Maximum time to wait for URL element
            
        Returns:
            str: Extracted URL or empty string if not found
        """
        try:
            print("Attempting to extract custom URL...")
            
            # First priority: Look for the format with SVG icon and potential "Not published" status
            url_xpath_priority = "//li[contains(@class, 'mt-2')]//span[contains(@class, 'flex')]//p[contains(text(), 'lovable.app')]"
            url_elements = self.driver.find_elements(By.XPATH, url_xpath_priority)
            
            if url_elements:
                # Extract just the URL part without the "Not published" text
                full_text = url_elements[0].text.strip()
                url_parts = full_text.split('\n')  # Split by newline to separate URL from status
                url_text = url_parts[0].strip()
                
                print(f"Found URL with priority format: {url_text}")
                # Check if it contains "lovable.app"
                if "lovable.app" in url_text:
                    return url_text
            
            # Second priority: Standard list item with lovable.app text
            url_xpath = "//li[contains(@class, 'mt-2')]//span[contains(text(), 'lovable.app')]"
            url_elements = self.driver.find_elements(By.XPATH, url_xpath)
            
            if url_elements:
                url_text = url_elements[0].text.strip()
                print(f"Found URL with standard format: {url_text}")
                return url_text
            
            # Third priority: Try other selectors that might find the URL
            alternate_selectors = [
                "//p[contains(text(), 'lovable.app')]",
                "//span[contains(text(), 'lovable.app')]",
                "//a[contains(@href, 'lovable.app')]",
                "//div[contains(@class, 'site-url')]//span",
                "//text()[contains(., 'lovable.app')]/.."
            ]
            
            for selector in alternate_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    for element in elements:
                        url_text = element.text.strip()
                        if "lovable.app" in url_text:
                            # If there's a newline, take just the first line (the URL)
                            if "\n" in url_text:
                                url_text = url_text.split("\n")[0].strip()
                            
                            print(f"Found URL with alternate selector: {url_text}")
                            return url_text
            
            # Last resort: Look for any text containing lovable.app in the page
            page_source = self.driver.page_source.lower()
            import re
            url_match = re.search(r'([a-z0-9-]+)\.lovable\.app', page_source)
            if url_match:
                url_text = f"{url_match.group(1)}.lovable.app"
                print(f"Found URL in page source: {url_text}")
                return url_text
            
            print("Could not find custom URL")
            return ""
            
        except Exception as e:
            print(f"Error extracting custom URL: {e}")
            # Take a screenshot for debugging
            try:
                debug_dir = os.path.join(os.getcwd(), "debug_screenshots")
                os.makedirs(debug_dir, exist_ok=True)
                screenshot_path = os.path.join(debug_dir, f"url_extract_error_{int(time.time())}.png")
                self.driver.save_screenshot(screenshot_path)
                print(f"Saved error screenshot to {screenshot_path}")
            except:
                pass
            return ""
    
    def save_project_info_to_file(self, url, description, filename):
        """
        Save the project URL and description to a file.
        
        Args:
            url: The custom URL
            description: The project description
            filename: Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(filename)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            # Write URL and description to file in append mode
            with open(filename, 'a', encoding='utf-8') as file:
                file.write(f"URL: {url}\n")
                file.write(f"Description: {description}\n")
                file.write("-" * 50 + "\n")
                
            print(f"Successfully saved project info to {filename}")
            return True
        except Exception as e:
            print(f"Failed to save project info to file: {e}")
            return False
