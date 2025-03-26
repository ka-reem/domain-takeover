import time
import os
import argparse
import csv
from urllib.parse import urlparse
import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

try:
    from config import CREDENTIALS, GROQ_API_KEY, GROQ_MODEL
    from automation.web_automation import WebsiteAutomation
    from automation.groq_processor import GroqProcessor
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you have the correct directory structure and required modules.")
    print("Copy config.example.py to config.py and update with your credentials.")
    exit(1)

def read_urls_from_csv(csv_path, limit=None):
    """Read URLs from a CSV file."""
    urls = []
    try:
        with open(csv_path, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            
            for row in csv_reader:
                if row and row[0].strip():  # Check if row exists and first cell is not empty
                    url = row[0].strip()
                    urls.append(url)
                    if limit and len(urls) >= limit:
                        break
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    
    return urls

def process_url(url, bot, groq_processor, output_dir, wait_time, domain_log_file):
    """
    Process a single URL to extract chat messages and generate a URL.
    
    Args:
        url: URL to process
        bot: WebsiteAutomation instance
        groq_processor: GroqProcessor instance
        output_dir: Directory to save output
        wait_time: Time to wait for page to load
        domain_log_file: File to log all domain names
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{'='*50}\nProcessing URL: {url}\n{'='*50}")
    
    try:
        # First check if we need to navigate
        current_url = bot.get_current_url()
        if current_url != url:
            print(f"Navigating to {url}")
            bot.navigate_to(url)
            
            # Wait to ensure the page loads
            print(f"Waiting for page to load completely... ({wait_time} seconds)")
            time.sleep(wait_time)
            
            # Check again if we're on the right page
            if not bot.is_on_correct_page(url):
                print("WARNING: May not be on the correct page. Attempting to navigate again...")
                bot.navigate_to(url)
                time.sleep(wait_time)
        
        # Extract the project ID for filename
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        filename_base = path_parts[-1] if len(path_parts) > 1 else "homepage"
        
        # Extract chat message (memory only, no file saving)
        extracted_text = bot.extract_chat_message_to_memory()
        
        if extracted_text:
            # Generate URL using Groq
            print(f"Generating domain name from extracted text using Groq...")
            generated_domain = groq_processor.generate_url(extracted_text)
            
            if generated_domain:
                # Print the domain name with emphasis
                print(f"\nDOMAIN NAME: {generated_domain}.com\n")
                
                # Log the domain to the consolidated file with lovable.app suffix
                with open(domain_log_file, "a", encoding="utf-8") as log_file:
                    log_file.write(f"{filename_base}: {generated_domain}.lovable.app\n")
                
                # 1. Press Escape first to exit any text field focus
                print("Pressing tab key to clear focus...")
                pyautogui.press('tab')
                time.sleep(0.5)  # Brief pause between keys
                
                # 2. Press Command + . to activate settings menu
                print("Pressing Command + . to activate settings menu")
                pyautogui.hotkey('command', '.')
                time.sleep(2)  # Wait for menu to appear
                
                # 3. Try to click the "Rename this project" button using Selenium
                try:
                    print("Looking for 'Rename this project' button...")
                    rename_button = bot.wait_for_element(
                        By.XPATH, 
                        "//button[contains(text(), 'Rename this project')]", 
                        timeout=5
                    )
                    
                    if rename_button:
                        rename_button.click()
                        print("Clicked 'Rename this project' button using Selenium")
                        time.sleep(1)  # Wait for rename dialog to appear
                        
                        # 4. Find the input field using class-based selector and enter "test"
                        input_selector = "input[name='newProjectName']"
                        input_field = bot.wait_for_element(
                            By.CSS_SELECTOR,
                            input_selector,
                            timeout=5
                        )
                        
                        if not input_field:
                            # Try alternative selector with class
                            input_field = bot.wait_for_element(
                                By.CSS_SELECTOR,
                                "input.rounded-md[placeholder='Enter new project name']",
                                timeout=5
                            )
                        
                        if input_field:
                            # First make sure the field is properly focused
                            input_field.click()
                            time.sleep(0.2)
                            
                            # Use keyboard shortcuts to select all existing text and delete it
                            if bot.driver.capabilities['platformName'].lower() == 'mac':
                                input_field.send_keys(Keys.COMMAND, 'a')  # Command+A (Select All on Mac)
                            else:
                                input_field.send_keys(Keys.CONTROL, 'a')  # Ctrl+A (Select All on Windows/Linux)
                            
                            time.sleep(0.2)
                            input_field.send_keys(Keys.DELETE)  # Delete selected text
                            time.sleep(0.2)
                            
                            # Now enter the generated domain
                            input_field.send_keys(generated_domain)
                            print(f"Entered '{generated_domain}' into rename field")
                            
                            # Press Enter to confirm
                            input_field.send_keys(Keys.RETURN)
                            print(f"Renamed project to '{generated_domain}'")
                            time.sleep(2)  # Wait for rename to complete
                            
                            # Check for console errors after renaming
                            has_errors, error_logs = bot.check_console_for_errors()
                            if has_errors:
                                print("⚠️ Detected console errors after renaming:")
                                for log in error_logs:
                                    print(f"  - {log.get('level')}: {log.get('message')}")
                                print("Domain name might already be taken or invalid.")
                                
                                # Try a fallback - add a random number to the domain
                                import random
                                fallback_domain = f"{generated_domain}{random.randint(1, 999)}"
                                print(f"Trying fallback domain: {fallback_domain}")
                                
                                # Try to open the rename dialog again
                                time.sleep(1)
                                
                                # Press Command + . again
                                print("Pressing Command + . again to activate settings menu")
                                pyautogui.hotkey('command', '.')
                                time.sleep(2)
                                
                                # Click rename button again
                                rename_button = bot.wait_for_element(
                                    By.XPATH, 
                                    "//button[contains(text(), 'Rename this project')]", 
                                    timeout=5
                                )
                                
                                if rename_button:
                                    rename_button.click()
                                    print("Clicked 'Rename this project' button again")
                                    time.sleep(1)
                                    
                                    # Find input field again
                                    input_field = bot.wait_for_element(
                                        By.CSS_SELECTOR,
                                        input_selector,
                                        timeout=5
                                    )
                                    
                                    if input_field:
                                        # Clear and enter fallback name
                                        input_field.click()
                                        time.sleep(0.2)
                                        
                                        # Select all and delete
                                        if bot.driver.capabilities['platformName'].lower() == 'mac':
                                            input_field.send_keys(Keys.COMMAND, 'a')
                                        else:
                                            input_field.send_keys(Keys.CONTROL, 'a')
                                        
                                        time.sleep(0.2)
                                        input_field.send_keys(Keys.DELETE)
                                        time.sleep(0.2)
                                        
                                        # Enter fallback domain name
                                        input_field.send_keys(fallback_domain)
                                        input_field.send_keys(Keys.RETURN)
                                        print(f"Used fallback domain name: {fallback_domain}")
                                        
                                        # Update the log file with the fallback domain
                                        with open(domain_log_file, "a", encoding="utf-8") as log_file:
                                            log_file.write(f"{filename_base}: {fallback_domain}.lovable.app (FALLBACK - original was taken)\n")
                                    
                            else:
                                print("No console errors detected, rename likely successful")
                        else:
                            print("Could not find rename input field")
                    else:
                        print("Could not find 'Rename this project' button, trying pyautogui fallback")
                        # Try to click at a position where the button might be
                        pyautogui.click(x=600, y=400)  # Adjust coordinates as needed
                        time.sleep(1)
                        
                        # Try typing the domain name and pressing Enter
                        pyautogui.write(generated_domain)
                        pyautogui.press('enter')
                        print(f"Used pyautogui fallback to attempt renaming to '{generated_domain}'")
                        
                except Exception as e:
                    print(f"Error during rename process: {e}")
                
                return True
            else:
                print("Failed to generate domain name from text")
                return False
        else:
            print(f"Failed to extract text from {url}")
            return False
            
    except Exception as e:
        print(f"An error occurred while processing {url}: {e}")
        return False

def main():
    """Main execution function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Extract chat messages and generate URLs")
    parser.add_argument('--url', help="Single URL of a Lovable.dev project (overrides CSV)")
    parser.add_argument('--csv', default="lovable-links.csv",
                        help="CSV file containing URLs (default: lovable-links.csv)")
    parser.add_argument('--limit', type=int, default=5,
                        help="Limit number of URLs to process (default: 5, 0 for all)")
    parser.add_argument('--headless', action='store_true', 
                        help="Run browser in headless mode (no GUI)")
    parser.add_argument('--output', default="extraction_results",
                        help="Directory to store results (default: extraction_results)")
    parser.add_argument('--left', action='store_true',
                        help="Position browser on the left side of screen (default is right side)")
    parser.add_argument('--wait', type=int, default=5,
                        help="Time to wait for page to load in seconds (default: 5)")
    args = parser.parse_args()
    
    # Create output directory
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # Create a single file to log all domains
    domain_log_file = os.path.join(args.output, "all_domains.txt")
    with open(domain_log_file, "w", encoding="utf-8") as f:
        f.write("# Project ID: Domain Name\n")
        f.write("# " + "="*50 + "\n\n")
    
    # Determine which URLs to process
    if args.url:
        urls = [args.url]
    else:
        # Process URLs from CSV
        limit = None if args.limit == 0 else args.limit
        urls = read_urls_from_csv(args.csv, limit)
        
        if not urls:
            print(f"No URLs found in {args.csv} or file doesn't exist.")
            exit(1)
            
        print(f"Found {len(urls)} URLs to process.")
    
    # Skip the homepage URL if it's in the list
    urls = [url for url in urls if not url.endswith("lovable.dev/")]
    
    # Initialize the Groq processor
    groq_processor = GroqProcessor(GROQ_API_KEY, GROQ_MODEL)
    
    # Track success/failure
    results = {"success": 0, "failure": 0, "total": len(urls)}
    
    # Initialize the browser with the first URL
    if urls:
        print(f"Initializing browser with first URL: {urls[0]}")
        bot = WebsiteAutomation(urls[0], headless=args.headless, position_right=not args.left)
        bot.start()
        
        try:
            # Perform login once at the beginning
            print("Logging in...")
            login_success = bot.quick_login(
                CREDENTIALS.get('email'),
                CREDENTIALS.get('password')
            )
            
            if not login_success:
                print("Failed to login. Exiting.")
                exit(1)
            
            # Process each URL
            for i, url in enumerate(urls, 1):
                print(f"\nProcessing URL {i}/{len(urls)}: {url}")
                success = process_url(url, bot, groq_processor, args.output, args.wait, domain_log_file)
                
                if success:
                    results["success"] += 1
                else:
                    results["failure"] += 1
                
                # Small delay between URLs
                if i < len(urls):
                    print("Waiting before processing next URL...")
                    time.sleep(3)
                
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Close browser
            bot.quit()
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"SUMMARY: Processed {results['total']} URLs")
        print(f"Success: {results['success']}")
        print(f"Failure: {results['failure']}")
        print(f"All domains saved to: {domain_log_file}")
        print(f"{'='*50}")
    else:
        print("No URLs to process.")

if __name__ == "__main__":
    main()
