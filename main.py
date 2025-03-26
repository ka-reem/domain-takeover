import time
import os
import argparse
import csv
from urllib.parse import urlparse

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

def process_url(url, bot, groq_processor, output_dir, wait_time):
    """
    Process a single URL to extract chat messages and generate a URL.
    
    Args:
        url: URL to process
        bot: WebsiteAutomation instance
        groq_processor: GroqProcessor instance
        output_dir: Directory to save output
        wait_time: Time to wait for page to load
        
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
        
        # File paths
        text_file = os.path.join(output_dir, f"text_{filename_base}.txt")
        url_file = os.path.join(output_dir, f"url_{filename_base}.txt")
        
        # Extract chat message
        extraction_success = bot.extract_chat_message(text_file)
        
        if extraction_success:
            # Read the extracted text
            with open(text_file, 'r', encoding='utf-8') as file:
                extracted_text = file.read()
                
            # Generate URL using Groq
            print(f"Generating domain name from extracted text using Groq...")
            generated_domain = groq_processor.generate_url(extracted_text)
            
            if generated_domain:
                # Print the domain name with emphasis
                print(f"\nDOMAIN NAME: {generated_domain}.com\n")
                
                # Save the domain name
                groq_processor.save_url_to_file(f"{generated_domain}.com", url_file)
                
                # Create a results summary
                with open(os.path.join(output_dir, "results_summary.txt"), "a", encoding="utf-8") as summary_file:
                    summary_file.write(f"{filename_base}: {generated_domain}.com\n")
                
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
                success = process_url(url, bot, groq_processor, args.output, args.wait)
                
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
        print(f"Results saved in: {args.output}")
        print(f"{'='*50}")
    else:
        print("No URLs to process.")

if __name__ == "__main__":
    main()
