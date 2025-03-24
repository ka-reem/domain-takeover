#!/usr/bin/env python3

def remove_duplicates(input_file, output_file=None):
    """
    Use linKlipper to extract all links from a webpage and save them to a CSV file.
    Removes duplicate URLs from the input file and saves unique URLs to the output file.
    If no output file is specified, it will overwrite the input file.
    """
    # Use the input file as output if no output file provided
    if output_file is None:
        output_file = input_file
    
    # Read all URLs from the file
    with open(input_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    # Get unique URLs while preserving original order
    unique_urls = []
    seen = set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    # Write unique URLs back to file
    with open(output_file, 'w') as f:
        for url in unique_urls:
            f.write(f"{url}\n")
    
    print(f"Removed {len(urls) - len(unique_urls)} duplicate URLs.")
    print(f"Original count: {len(urls)}, Unique count: {len(unique_urls)}")

if __name__ == "__main__":
    # # Input and output file paths
    csv_file = "lovable-links.csv"
    # output_file = "lovable-links-unique.csv"
    
    # To overwrite the original file, use:
    remove_duplicates(csv_file)
    
    # To save to a new file:
    # remove_duplicates(csv_file, output_file)
    print(f"Unique URLs saved to {csv_file}")
