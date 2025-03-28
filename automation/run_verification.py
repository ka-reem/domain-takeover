import os
import sys
import argparse
from verification_automation import VerificationAutomation

def main():
    """Run the verification automation with command line arguments"""
    parser = argparse.ArgumentParser(description='Automated website verification tool')
    
    # Required arguments
    parser.add_argument('--urls', required=True, help='Path to file containing URLs to verify (one URL per line)')
    
    # Optional arguments
    parser.add_argument('--output', default='verification_results', 
                        help='Directory to save verification results')
    parser.add_argument('--login', action='store_true', 
                        help='Enable login before verification')
    parser.add_argument('--login-url', help='URL for the login page')
    parser.add_argument('--email', help='Email for login')
    parser.add_argument('--password', help='Password for login')
    parser.add_argument('--headless', action='store_true', 
                        help='Run in headless mode (no browser UI)')
    parser.add_argument('--start', type=int, default=0,
                        help='Start processing from this index in the URL file (default: 0)')
    parser.add_argument('--limit', type=int, default=0,
                        help='Limit number of URLs to process (default: 0 for all)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not os.path.isfile(args.urls):
        print(f"Error: URL file not found: {args.urls}")
        return 1
    
    if args.login and (not args.login_url or not args.email or not args.password):
        print("Error: When --login is enabled, --login-url, --email, and --password are required")
        return 1
    
    # Create output directory if it doesn't exist
    output_dir = args.output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Read URLs from file
    with open(args.urls, 'r') as f:
        all_urls = [line.strip() for line in f if line.strip()]
    
    if not all_urls:
        print("Error: No URLs found in the specified file.")
        return 1
    
    # Apply start and limit parameters
    start_idx = min(args.start, len(all_urls))
    if args.limit > 0:
        end_idx = min(start_idx + args.limit, len(all_urls))
        urls = all_urls[start_idx:end_idx]
    else:
        urls = all_urls[start_idx:]
    
    print(f"Loaded {len(urls)} URLs from {args.urls} (starting at index {start_idx})")
    
    # Initialize the verifier
    verifier = VerificationAutomation(headless=args.headless)
    
    try:
        # Login if required
        if args.login:
            print(f"Attempting login at {args.login_url}")
            login_success = verifier.login(args.login_url, args.email, args.password)
            if not login_success:
                print("Login failed. Exiting.")
                return 1
            print("Login successful!")
        
        # Process the URLs
        print(f"Starting verification of {len(urls)} URLs...")
        results = verifier.process_url_list(urls, output_dir)
        
        # Print summary
        print("\nVerification Results Summary:")
        success_count = sum(1 for success in results.values() if success)
        print(f"Total URLs: {len(urls)}")
        print(f"Successful verifications: {success_count}")
        print(f"Failed verifications: {len(urls) - success_count}")
        print(f"Results saved to: {output_dir}")
        
        return 0
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"An error occurred: {e}")
        return 1
    finally:
        # Always quit the browser when done
        verifier.quit()

if __name__ == "__main__":
    sys.exit(main())
