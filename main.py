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

def read_urls_from_csv(csv_path, start_index=0, limit=None):
    """
    Read URLs from a CSV file.
    
    Args:
        csv_path: Path to the CSV file
        start_index: Index to start reading URLs from (0-based)
        limit: Maximum number of URLs to read
    
    Returns:
        list: List of URLs
    """
    urls = []
    try:
        with open(csv_path, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            
            # Skip URLs before the start_index
            for i, row in enumerate(csv_reader):
                if i < start_index:
                    continue
                    
                if row and row[0].strip():  # Check if row exists and first cell is not empty
                    url = row[0].strip()
                    urls.append(url)
                    
                    # Stop once we have enough URLs
                    if limit and len(urls) >= limit:
                        break
                        
            print(f"Read {len(urls)} URLs from {csv_path} (starting at index {start_index})")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    
    return urls

def attempt_rename(bot, input_selector, domain_name):
    """
    Attempt to rename a project with the given domain name.
    
    Args:
        bot: WebsiteAutomation instance
        input_selector: CSS selector for the input field
        domain_name: Domain name to use
        
    Returns:
        tuple: (success, has_errors)
    """
    # Find the input field
    input_field = bot.wait_for_element(
        By.CSS_SELECTOR,
        input_selector,
        timeout=3  # Reduced from 5
    )
    
    if not input_field:
        # Try alternative selector with class
        input_field = bot.wait_for_element(
            By.CSS_SELECTOR,
            "input.rounded-md[placeholder='Enter new project name']",
            timeout=3  # Reduced from 5
        )
    
    if input_field:
        # First make sure the field is properly focused
        input_field.click()
        time.sleep(0.1)  # Reduced from 0.2
        
        # Use keyboard shortcuts to select all existing text and delete it
        if bot.driver.capabilities['platformName'].lower() == 'mac':
            input_field.send_keys(Keys.COMMAND, 'a')  # Command+A (Select All on Mac)
        else:
            input_field.send_keys(Keys.CONTROL, 'a')  # Ctrl+A (Select All on Windows/Linux)
        
        time.sleep(0.1)  # Reduced from 0.2
        input_field.send_keys(Keys.DELETE)  # Delete selected text
        time.sleep(0.1)  # Reduced from 0.2
        
        # Now enter the generated domain
        input_field.send_keys(domain_name)
        print(f"Entered '{domain_name}' into rename field")
        
        # Press Enter to confirm
        input_field.send_keys(Keys.RETURN)
        print(f"Attempted rename to '{domain_name}'")
        time.sleep(1.5)  # Reduced from 2
        
        # Check for console errors after renaming
        has_errors, error_logs = bot.check_console_for_errors()
        if has_errors:
            print("⚠️ Detected console errors after renaming:")
            for log in error_logs:
                print(f"  - {log.get('level')}: {log.get('message')}")
            print("Domain name might already be taken or invalid.")
            return False, True
        else:
            print("No console errors detected, rename successful")
            return True, False
    else:
        print("Could not find rename input field")
        return False, False

def try_multiple_domains(bot, groq_processor, original_domain, original_text, url, wait_time, custom_prompt=None):
    """
    Try multiple domain names until one works.
    
    Args:
        bot: WebsiteAutomation instance
        groq_processor: GroqProcessor instance
        original_domain: The domain name that failed
        original_text: The original text content to base alternatives on
        url: The current project URL
        wait_time: Time to wait for page to load
        custom_prompt: Optional custom prompt to use for domain generation
        
    Returns:
        tuple: (success, domain_name)
    """
    # Generate a list of 20 alternative domains based on the original text
    alternative_domains = groq_processor.generate_alternative_domains(
        original_domain, 
        original_text, 
        count=20, 
        custom_prompt=custom_prompt
    )
    
    # Find the input field (assuming we're already in it)
    input_field = bot.wait_for_element(
        By.CSS_SELECTOR,
        "input[name='newProjectName']",
        timeout=3  # Reduced from 5
    )
    
    if not input_field:
        input_field = bot.wait_for_element(
            By.CSS_SELECTOR,
            "input.rounded-md[placeholder='Enter new project name']",
            timeout=3  # Reduced from 5
        )
    
    if not input_field:
        print("Could not find input field for renaming")
        return False, None
    
    # We're already in the rename dialog with the input field focused
    print("Starting to try alternative domain names in the existing input field")
    
    # Try each alternative domain
    for i, domain in enumerate(alternative_domains, 1):
        print(f"\nTrying alternative domain {i}/{len(alternative_domains)}: {domain}")
        
        # 1. Clear the field (select all text and delete it)
        input_field.click()
        time.sleep(0.1)  # Reduced from 0.2
        
        if bot.driver.capabilities['platformName'].lower() == 'mac':
            input_field.send_keys(Keys.COMMAND, 'a')
        else:
            input_field.send_keys(Keys.CONTROL, 'a')
            
        time.sleep(0.1)  # Reduced from 0.2
        input_field.send_keys(Keys.DELETE)
        time.sleep(0.1)  # Reduced from 0.2
        
        # 2. Enter the alternative domain name
        input_field.send_keys(domain)
        print(f"Entered alternative domain name: {domain}")
        
        # 3. Press Enter to submit
        input_field.send_keys(Keys.RETURN)
        print(f"Pressed Enter to submit '{domain}'")
        time.sleep(1.5)  # Reduced from 2
        
        # 4. Check for console errors
        has_errors, _ = bot.check_console_for_errors()
        if not has_errors:
            print(f"Domain '{domain}' appears to work!")
            return True, domain
        else:
            print(f"Domain '{domain}' was rejected, trying next one...")
            
            # Important: Find the input field again, as the page might have refreshed
            input_field = bot.wait_for_element(
                By.CSS_SELECTOR,
                "input[name='newProjectName']",
                timeout=3  # Reduced from 5
            )
            
            if not input_field:
                input_field = bot.wait_for_element(
                    By.CSS_SELECTOR,
                    "input.rounded-md[placeholder='Enter new project name']",
                    timeout=3  # Reduced from 5
                )
                
            if not input_field:
                print("Lost the input field after trying domain, can't continue")
                return False, None
    
    # If we get here, none of the domains worked
    print(f"None of the {len(alternative_domains)} alternative domains worked")
    return False, None

def process_url(url, bot, groq_processor, output_dir, wait_time, domain_log_file, custom_prompt=None):
    """
    Process a single URL to extract chat messages and generate a URL.
    
    Args:
        url: URL to process
        bot: WebsiteAutomation instance
        groq_processor: GroqProcessor instance
        output_dir: Directory to save output
        wait_time: Time to wait for page to load
        domain_log_file: File to log all domain names
        custom_prompt: Optional custom prompt to use for domain generation
        
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
            # Initial attempt with first domain name
            success = False
            final_domain = None
            
            # Generate URL using Groq with optional custom prompt
            print(f"Generating domain name from extracted text using Groq...")
            if custom_prompt:
                print(f"Using custom prompt: \"{custom_prompt[:100]}...\"")
            generated_domain = groq_processor.generate_url(extracted_text, custom_prompt)
            
            if generated_domain:
                # Print the domain name with emphasis
                print(f"\nDOMAIN NAME: {generated_domain}.com\n")
                
                # 1. Press Escape first to exit any text field focus
                print("Pressing tab key to clear focus...")
                pyautogui.press('tab')
                time.sleep(0.3)  # Reduced from 0.5
                
                # 2. Press Command + . to activate settings menu
                print("Pressing Command + . to activate settings menu")
                pyautogui.hotkey('command', '.')
                time.sleep(1)  # Reduced from 2
                
                # 3. Try to click the "Rename this project" button using Selenium
                try:
                    print("Looking for 'Rename this project' button...")
                    rename_button = bot.wait_for_element(
                        By.XPATH, 
                        "//button[contains(text(), 'Rename this project')]", 
                        timeout=3  # Reduced from 5
                    )
                    
                    if rename_button:
                        rename_button.click()
                        print("Clicked 'Rename this project' button using Selenium")
                        time.sleep(0.5)  # Reduced from 1
                        
                        # 4. Attempt to rename with first generated domain
                        success, has_errors = attempt_rename(
                            bot, 
                            "input[name='newProjectName']", 
                            generated_domain
                        )
                        
                        if success:
                            # First attempt succeeded
                            final_domain = generated_domain
                        elif has_errors:
                            # First domain name was rejected, try alternatives
                            print(f"Domain '{generated_domain}' was rejected. Trying alternatives...")
                            
                            # Pass custom prompt to try_multiple_domains
                            success, final_domain = try_multiple_domains(
                                bot, groq_processor, generated_domain, extracted_text, url, wait_time, custom_prompt
                            )
                    else:
                        print("Could not find 'Rename this project' button")
                except Exception as e:
                    print(f"Error during rename process: {e}")
            else:
                print("Failed to generate initial domain name")
            
            # Record the results
            if success and final_domain:
                # Log the domain to the consolidated file with lovable.app suffix
                with open(domain_log_file, "a", encoding="utf-8") as log_file:
                    log_file.write(f"{filename_base}: {final_domain}.lovable.app\n")
                
                print(f"Successfully renamed project to '{final_domain}'")
                return True
            else:
                print(f"Failed to rename project after trying multiple domain names")
                with open(domain_log_file, "a", encoding="utf-8") as log_file:
                    log_file.write(f"{filename_base}: FAILED - Could not find a working domain name\n")
                return False
        else:
            print(f"Failed to extract text from {url}")
            return False
            
    except Exception as e:
        print(f"An error occurred while processing {url}: {e}")
        return False

def publish_projects(csv_path, output_path, start_index=0, limit=None, headless=False, position_left=False, wait_time=5):
    """
    Publish projects from a CSV list by clicking on the publish button.
    
    Args:
        csv_path: Path to CSV file containing URLs
        output_path: Path to save results
        start_index: Index to start from in the CSV file
        limit: Maximum number of URLs to process
        headless: Whether to run in headless mode
        position_left: Whether to position browser on left side of screen
        wait_time: Time to wait for page to load in seconds
    
    Returns:
        dict: Results with success/failure counts
    """
    # Read URLs from CSV
    urls = read_urls_from_csv(csv_path, start_index, limit)
    
    if not urls:
        print(f"No URLs found in {csv_path} starting at index {start_index}, or file doesn't exist.")
        return {"success": 0, "failure": 0, "total": 0}
    
    # Create output directory and results file
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    results_file = os.path.join(output_path, "publish_results.txt")
    with open(results_file, "a", encoding="utf-8") as f:
        f.write(f"\n# New publishing batch starting at index {start_index} with limit {limit}\n")
        f.write(f"# {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# " + "="*50 + "\n\n")
    
    # Create a separate file for project info (URL + description)
    project_info_file = os.path.join(output_path, "project_info.txt")
    with open(project_info_file, "a", encoding="utf-8") as f:
        f.write(f"\n# Project info batch starting at index {start_index} with limit {limit}\n")
        f.write(f"# {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# " + "="*50 + "\n\n")
    
    # Track success/failure
    results = {"success": 0, "failure": 0, "total": len(urls)}
    
    # Initialize the browser with the first URL
    if urls:
        print(f"Initializing browser with first URL: {urls[0]}")
        bot = WebsiteAutomation(urls[0], headless=headless, position_right=not position_left)
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
                return results
            
            # Process each URL
            for i, url in enumerate(urls, 1):
                print(f"\nPublishing URL {i}/{len(urls)}: {url}")
                
                try:
                    # Navigate to the URL
                    success = bot.navigate_to(url)
                    
                    if not success:
                        print(f"Failed to navigate to {url}")
                        with open(results_file, "a", encoding="utf-8") as f:
                            f.write(f"{url}: FAILED - Could not navigate to URL\n")
                        results["failure"] += 1
                        continue
                    
                    # Wait for page to load
                    print(f"Waiting for page to load... ({wait_time} seconds)")
                    time.sleep(wait_time)
                    
                    # Extract custom URL before publishing
                    custom_url = bot.extract_custom_url()
                    
                    # Take a screenshot before clicking
                    screenshot_dir = os.path.join(output_path, "screenshots")
                    if not os.path.exists(screenshot_dir):
                        os.makedirs(screenshot_dir)
                    
                    # Create screenshot filename based on URL
                    domain = urlparse(url).netloc
                    path = urlparse(url).path.replace('/', '_')
                    screenshot_file = os.path.join(screenshot_dir, f"{domain}{path}_before.png")
                    bot.driver.save_screenshot(screenshot_file)
                    
                    # STEP 1: Click the publish button first (using the updated XPath)
                    publish_button = bot.wait_for_element(
                        By.XPATH, 
                        "/html/body/div[1]/div/div[2]/nav/div/div/div/div[2]/div[3]/div/button[3]", 
                        timeout=5
                    )
                    
                    # If button not found with specific XPath, try more generic XPath
                    if not publish_button:
                        print("Specific publish button not found, trying alternative XPaths...")
                        
                        # Try several alternative XPaths for publish button
                        publish_xpath_alternatives = [
                            "//nav//button[3]",
                            "//button[contains(text(), 'Publish')]",
                            "//button[contains(@aria-label, 'publish')]",
                            "//div[contains(@class, 'header')]//button[3]",
                            "//nav//div//div//div//div[2]//div[3]//div//button[last()]"
                        ]
                        
                        for xpath in publish_xpath_alternatives:
                            publish_button = bot.wait_for_element(By.XPATH, xpath, timeout=2)
                            if publish_button:
                                print(f"Found publish button using alternative XPath: {xpath}")
                                break
                    
                    if publish_button:
                        # Click the publish button
                        publish_button.click()
                        print("Clicked the publish button")
                        
                        # Wait for menu to appear
                        time.sleep(1)
                        
                        # Extract description after clicking publish but before confirming
                        description = bot.extract_project_description()
                        
                        # If custom URL wasn't extracted earlier, try again now
                        if not custom_url:
                            custom_url = bot.extract_custom_url()
                        
                        # STEP 2: Now click the confirm publish button - Use more reliable selectors first
                        # Start with the most generic and reliable XPaths instead of hard-coded IDs
                        confirm_xpath_alternatives = [
                            "//div[@role='menu']/div[2]/button[1]",  # This is the one that works consistently
                            "//div[contains(@class, 'dropdown') or contains(@class, 'menu')]/div[2]/button[1]",
                            "//button[contains(text(), 'Publish') and not(contains(@aria-label, 'settings'))]",
                            "//div[contains(@role, 'menu')]//button[contains(., 'Publish')]",
                            "//div[contains(@class, 'ContextMenu')]/div[2]/button[1]",
                            # Only try the specific ID as a last resort
                            "//*[@id='radix-:r32:']/div[2]/button[1]"  
                        ]
                        
                        confirm_button = None
                        for xpath in confirm_xpath_alternatives:
                            confirm_button = bot.wait_for_element(By.XPATH, xpath, timeout=2)
                            if confirm_button:
                                print(f"Found confirm button using XPath: {xpath}")
                                break
                        
                        if confirm_button:
                            # Click the confirm button
                            confirm_button.click()
                            print("Clicked the confirm publish button")
                            
                            # Wait for publish operation to complete
                            print("Waiting for publish operation to complete...")
                            time.sleep(0.5)
                            
                            # Take another screenshot after clicking
                            screenshot_after = os.path.join(screenshot_dir, f"{domain}{path}_after.png")
                            bot.driver.save_screenshot(screenshot_after)
                            
                            # Try to extract custom URL again if not successful before
                            if not custom_url:
                                custom_url = bot.extract_custom_url()
                            
                            # Check console logs for any errors
                            has_errors, error_logs = bot.check_console_for_errors()
                            
                            # Save project info to file
                            if custom_url or description:
                                bot.save_project_info_to_file(custom_url, description, project_info_file)
                            
                            if has_errors:
                                print("⚠️ Detected console errors after publishing:")
                                for log in error_logs[:3]:  # Show only first 3 errors
                                    print(f"  - {log.get('level')}: {log.get('message')}")
                                
                                with open(results_file, "a", encoding="utf-8") as f:
                                    f.write(f"{url}: WARNING - Published but detected console errors\n")
                                
                                # Still count as success since button was clicked
                                results["success"] += 1
                            else:
                                print("Published successfully with no console errors")
                                with open(results_file, "a", encoding="utf-8") as f:
                                    f.write(f"{url}: SUCCESS - Published successfully\n")
                                    if custom_url:
                                        f.write(f"       Custom URL: {custom_url}\n")
                                results["success"] += 1
                        else:
                            print("Could not find confirm publish button")
                            with open(results_file, "a", encoding="utf-8") as f:
                                f.write(f"{url}: FAILED - Could not find confirm publish button\n")
                            results["failure"] += 1
                    else:
                        print("Could not find publish button")
                        with open(results_file, "a", encoding="utf-8") as f:
                            f.write(f"{url}: FAILED - Could not find publish button\n")
                        results["failure"] += 1
                
                except Exception as e:
                    print(f"Error publishing {url}: {e}")
                    with open(results_file, "a", encoding="utf-8") as f:
                        f.write(f"{url}: ERROR - {str(e)}\n")
                    results["failure"] += 1
                
                # Small delay between URLs
                if i < len(urls):
                    print("Waiting before processing next URL...")
                    time.sleep(1.5)  # Reduced from 3
        
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Close browser
            bot.quit()
    
    # Update the final summary with project info file path
    results["project_info_file"] = project_info_file
    return results

def main():
    """Main execution function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Lovable.dev Automation Tool")
    parser.add_argument('action', choices=['extract', 'publish'], 
                        help="Action to perform: extract (text and generate URLs) or publish (projects)")
    parser.add_argument('--url', help="Single URL of a Lovable.dev project (overrides CSV)")
    parser.add_argument('--csv', default="lovable-links.csv",
                        help="CSV file containing URLs (default: lovable-links.csv)")
    parser.add_argument('--start', type=int, default=0,
                        help="Start processing from this index in the CSV file (default: 0)")
    parser.add_argument('--limit', type=int, default=5,
                        help="Limit number of URLs to process (default: 5, 0 for all)")
    parser.add_argument('--headless', action='store_true', 
                        help="Run browser in headless mode (no GUI)")
    parser.add_argument('--output', default="automation_results",
                        help="Directory to store results (default: automation_results)")
    parser.add_argument('--left', action='store_true',
                        help="Position browser on the left side of screen (default is right side)")
    parser.add_argument('--wait', type=int, default=5,
                        help="Time to wait for page to load in seconds (default: 5)")
    parser.add_argument('--prompt', 
                        help="Custom AI prompt for domain name generation")
    parser.add_argument('--prompt-file',
                        help="Path to a file containing a custom AI prompt")
    args = parser.parse_args()
    
    # Create the base output directory
    output_dir = os.path.join(args.output, args.action)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process based on action
    if args.action == 'extract':
        # Handle custom prompt options
        custom_prompt = None
        if args.prompt:
            custom_prompt = args.prompt
            print(f"Using custom prompt from command line: \"{custom_prompt[:100]}...\"")
        elif args.prompt_file:
            try:
                with open(args.prompt_file, 'r', encoding='utf-8') as f:
                    custom_prompt = f.read().strip()
                    print(f"Using custom prompt from file: \"{custom_prompt[:100]}...\"")
            except Exception as e:
                print(f"Error reading prompt file: {e}")
                print("Falling back to default prompts.")
        
        # Create a single file to log all domains - always in append mode to avoid overwriting
        domain_log_file = os.path.join(output_dir, "all_domains.txt")
        
        # Create the file with headers if it doesn't exist
        if not os.path.exists(domain_log_file):
            with open(domain_log_file, "w", encoding="utf-8") as f:
                f.write("# Project ID: Domain Name\n")
                f.write("# " + "="*50 + "\n")
        
        # Always append to existing file
        with open(domain_log_file, "a", encoding="utf-8") as f:
            f.write(f"\n# New processing batch starting at index {args.start} with limit {args.limit}\n")
            f.write(f"# {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# " + "="*50 + "\n\n")
        
        # Determine which URLs to process
        if args.url:
            urls = [args.url]
        else:
            # Process URLs from CSV starting at the specified index
            limit = None if args.limit == 0 else args.limit
            urls = read_urls_from_csv(args.csv, args.start, limit)
            
            if not urls:
                print(f"No URLs found in {args.csv} starting at index {args.start}, or file doesn't exist.")
                exit(1)
                
            print(f"Found {len(urls)} URLs to process, starting from index {args.start}.")
        
        # Skip the homepage URL if it's in the list
        urls = [url for url in urls if not url.endswith("lovable.dev/")]
        
        # Initialize the Groq processor
        groq_processor = GroqProcessor(GROQ_API_KEY, GROQ_MODEL)
        
        # Track success/failure
        results = {"success": 0, "failure": 0, "total": len(urls)}
        
        # Display the range of URLs being processed
        if len(urls) > 0:
            print(f"Processing URLs {args.start+1} to {args.start+len(urls)} from the CSV")
        
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
                    success = process_url(
                        url, 
                        bot, 
                        groq_processor, 
                        output_dir, 
                        args.wait, 
                        domain_log_file,
                        custom_prompt
                    )
                    
                    if success:
                        results["success"] += 1
                    else:
                        results["failure"] += 1
                    
                    # Small delay between URLs
                    if i < len(urls):
                        print("Waiting before processing next URL...")
                        time.sleep(1.5)  # Reduced from 3
                    
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
    
    elif args.action == 'publish':
        print(f"Starting publish operation on URLs from {args.csv}")
        
        # Run the publish operation
        limit = None if args.limit == 0 else args.limit
        results = publish_projects(
            args.csv,
            output_dir,
            args.start,
            limit,
            args.headless,
            args.left,
            args.wait
        )
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"PUBLISH SUMMARY: Processed {results['total']} URLs")
        print(f"Success: {results['success']}")
        print(f"Failure: {results['failure']}")
        print(f"Results saved to: {os.path.join(output_dir, 'publish_results.txt')}")
        if "project_info_file" in results:
            print(f"Project info (URLs and descriptions) saved to: {results['project_info_file']}")
        print(f"{'='*50}")

if __name__ == "__main__":
    main()
