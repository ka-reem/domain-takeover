import time
import os
import argparse

try:
    from config import CREDENTIALS
    from automation.web_automation import WebsiteAutomation
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you have the correct directory structure and required modules.")
    print("Copy config.example.py to config.py and update with your credentials.")
    exit(1)

def main():
    """Main execution function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Extract chat messages from Lovable.dev projects")
    parser.add_argument('--url', default="https://lovable.dev/projects/-",
                        help="URL of the Lovable.dev project (default: example project)")
    parser.add_argument('--headless', action='store_true', 
                        help="Run browser in headless mode (no GUI)")
    parser.add_argument('--output', default="chat_extraction_results",
                        help="Directory to store results (default: chat_extraction_results)")
    parser.add_argument('--left', action='store_true',
                        help="Position browser on the left side of screen (default is right side)")
    args = parser.parse_args()
    
    # Create output directory
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # Create bot instance and start
    print(f"Starting automation for {args.url}")
    bot = WebsiteAutomation(args.url, headless=args.headless, position_right=not args.left)
    bot.start()
    
    try:
        # Login with credentials from config
        success = bot.quick_login(
            CREDENTIALS.get('email'),
            CREDENTIALS.get('password')
        )
        
        # Wait for page to fully load
        if success:
            print("Waiting for page to load completely...")
            time.sleep(10)
            
            # Extract chat message
            output_file = os.path.join(args.output, f"chat_{os.path.basename(args.url)}.txt")
            bot.extract_chat_message(output_file)
            
            print(f"\nExtraction complete. Results saved in '{args.output}' directory.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close browser
        time.sleep(2)
        bot.quit()

if __name__ == "__main__":
    main()
