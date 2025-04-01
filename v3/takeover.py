import os
import time
import csv
import argparse
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pyautogui

# Add parent directory to Python path to import modules from there
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Import from parent directory (root)
    from config import CREDENTIALS
    from automation.web_automation import WebsiteAutomation
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you have the correct directory structure and required modules.")
    print("Copy config.example.py to config.py and update with your credentials.")
    exit(1)

def read_domains_from_csv(csv_path):
    """Read domain names from a CSV file."""
    domains = []
    try:
        with open(csv_path, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                if row and row[0].strip():
                    domains.append(row[0].strip())
        print(f"Read {len(domains)} domain names from {csv_path}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return domains

def read_domains_from_txt(txt_path):
    """Read domain names from a plain text file."""
    domains = []
    try:
        with open(txt_path, 'r') as txtfile:
            for line in txtfile:
                domain = line.strip()
                if domain:
                    domains.append(domain)
        print(f"Read {len(domains)} domain names from {txt_path}")
    except Exception as e:
        print(f"Error reading text file: {e}")
    return domains

def attempt_rename(bot, domain_name):
    """Attempt to rename a project with the given domain name."""
    # Find the input field
    input_field = bot.wait_for_element(
        By.CSS_SELECTOR,
        "input[name='newProjectName'], input.rounded-md[placeholder='Enter new project name']",
        timeout=3
    )
    
    if input_field:
        # Focus and clear field
        input_field.click()
        time.sleep(0.1)
        
        # Select all text and delete it
        if bot.driver.capabilities['platformName'].lower() == 'mac':
            input_field.send_keys(Keys.COMMAND, 'a')
        else:
            input_field.send_keys(Keys.CONTROL, 'a')
        
        input_field.send_keys(Keys.DELETE)
        time.sleep(0.1)
        
        # Enter domain name and submit
        input_field.send_keys(domain_name)
        print(f"Entered '{domain_name}' into rename field")
        input_field.send_keys(Keys.RETURN)
        print(f"Attempted rename to '{domain_name}'")
        time.sleep(1.5)
        
        # Check for console errors
        has_errors, error_logs = bot.check_console_for_errors()
        if has_errors:
            print("⚠️ Detected console errors after renaming:")
            for log in error_logs[:2]:  # Show first 2 errors only
                print(f"  - {log.get('level')}: {log.get('message')}")
            print("Domain name might already be taken or invalid.")
            return False, True
        else:
            print("No console errors detected, rename successful")
            return True, False
    else:
        print("Could not find rename input field")
        return False, False

def takeover_domain(url, bot, domains_list, output_file, wait_time=5):
    """Process a URL to take over its domain."""
    print(f"\n{'='*50}\nAttempting domain takeover on: {url}\n{'='*50}")
    
    try:
        # Navigate to URL and wait for page load
        print(f"Navigating to {url}")
        if not bot.navigate_to(url):
            print(f"Failed to navigate to {url}")
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"{url}: FAILED - Could not navigate to URL\n")
            return False
        
        print(f"Waiting for page to load... ({wait_time} seconds)")
        time.sleep(wait_time)
        
        # Open settings menu once at the beginning
        print("Opening settings menu...")
        pyautogui.press('tab')
        time.sleep(0.3)
        pyautogui.hotkey('command', '.')
        time.sleep(1)
        
        successful_domains = []
        
        # Try each domain name
        for i, domain in enumerate(domains_list, 1):
            print(f"\nAttempting domain name {i}/{len(domains_list)}: {domain}")
            
            # Find and click "Rename project" button
            print("Looking for 'Rename project' button...")
            rename_button = None
            
            # Try different methods to find the button
            for selector in [
                (By.XPATH, '//*[@id="radix-:r4n:-content-settings"]/div/button[1]'),
                (By.XPATH, "//button[contains(text(), 'Rename project')]"),
                (By.CSS_SELECTOR, "button.hover\\:bg-neutral-100")
            ]:
                rename_button = bot.wait_for_element(selector[0], selector[1], timeout=1)
                if rename_button:
                    break
            
            if not rename_button:
                print("Could not find 'Rename project' button")
                continue
            
            rename_button.click()
            print("Clicked 'Rename project' button")
            time.sleep(0.5)
            
            # Attempt rename
            rename_success, has_errors = attempt_rename(bot, domain)
            
            if rename_success:
                print(f"✅ Successfully renamed project to '{domain}'")
                successful_domains.append(domain)
                
                # Record successful domain
                with open("successful_domains.txt", "a", encoding="utf-8") as sf:
                    sf.write(f"{domain}\n")
                
                # Don't do anything special after success, the settings menu should still be open
                # Just continue to the next iteration where we'll click "Rename project" again
                
            else:
                if has_errors:
                    print(f"❌ Domain '{domain}' was rejected, closing dialog and retrying...")
                    # Just press escape to close the dialog and try the next domain
                    pyautogui.press('escape')
                else:
                    print("Rename input field issue, trying to recover...")
                    # Try to escape any dialog and continue
                    pyautogui.press('escape')
                
                # Give time for dialog to close
                time.sleep(1)
        
        # After trying all domains, we don't need to save changes
        # The changes are applied immediately after each successful rename
        
        # Log results
        with open(output_file, "a", encoding="utf-8") as f:
            if successful_domains:
                domains_str = ", ".join(successful_domains)
                f.write(f"{url}: SUCCESS - Renamed to: {domains_str}\n")
                for domain in successful_domains:
                    f.write(f"  - {domain}\n")
            else:
                f.write(f"{url}: FAILED - Could not apply any domain name\n")
        
        return len(successful_domains) > 0
        
    except Exception as e:
        print(f"An error occurred: {e}")
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{url}: ERROR - {str(e)}\n")
        return False

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Domain Takeover Tool")
    parser.add_argument('--url', required=True, help="URL of the Lovable.dev project to take over")
    parser.add_argument('--csv', help="CSV file containing domain names to use")
    parser.add_argument('--txt', help="Text file containing domain names to use")
    parser.add_argument('--output', default="takeover_results.txt",
                        help="File to store takeover results (default: takeover_results.txt)")
    parser.add_argument('--headless', action='store_true', 
                        help="Run browser in headless mode (no GUI)")
    parser.add_argument('--left', action='store_true',
                        help="Position browser on the left side of screen (default is right side)")
    parser.add_argument('--wait', type=int, default=5,
                        help="Time to wait for page to load in seconds (default: 5)")
    args = parser.parse_args()
    
    # Check that either CSV or TXT file is provided
    if not args.csv and not args.txt:
        print("Error: You must provide either --csv or --txt argument")
        exit(1)
        
    # Set input file and read domain names
    input_file = args.csv if args.csv else args.txt
    
    if args.csv:
        if not os.path.isfile(args.csv):
            print(f"Error: CSV file not found: {args.csv}")
            exit(1)
        domains = read_domains_from_csv(args.csv)
    else:
        if not os.path.isfile(args.txt):
            print(f"Error: Text file not found: {args.txt}")
            exit(1)
        domains = read_domains_from_txt(args.txt)
    
    if not domains:
        print(f"No domain names found in {input_file}. Exiting.")
        exit(1)
    
    # Setup output file
    if not os.path.exists(args.output):
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("# URL: Takeover Result\n")
            f.write("# " + "="*50 + "\n\n")
    
    with open(args.output, "a", encoding="utf-8") as f:
        f.write(f"\n# New takeover attempt - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Target URL: {args.url}\n")
        f.write(f"# Domain names from: {input_file}\n")
        f.write("# " + "="*50 + "\n\n")
    
    # Initialize browser and start takeover process
    print(f"Initializing browser with URL: {args.url}")
    bot = WebsiteAutomation(args.url, headless=args.headless, position_right=not args.left)
    bot.start()
    
    try:
        print("Logging in...")
        if not bot.quick_login(CREDENTIALS.get('email'), CREDENTIALS.get('password')):
            print("Failed to login. Exiting.")
            exit(1)
        
        print("Login successful! Proceeding with domain takeover...")
        
        success = takeover_domain(args.url, bot, domains, args.output, args.wait)
        
        if success:
            print("\n🎉 Domain takeover successful!")
        else:
            print("\n❌ Domain takeover failed.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        bot.quit()

if __name__ == "__main__":
    main()
