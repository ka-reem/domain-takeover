"""
This module handles interactions with the Groq API
"""
import os
import json
from typing import Optional
import groq

class GroqProcessor:
    """Handles text processing using Groq API"""
    
    def __init__(self, api_key: str, model: str):
        """
        Initialize the Groq API client
        
        Args:
            api_key: Groq API key
            model: Groq model to use
        """
        self.client = groq.Groq(api_key=api_key)
        self.model = model
    
    def generate_url(self, text: str) -> Optional[str]:
        """
        Generate a short, simple, memorable URL based on the given text
        
        Args:
            text: Text content to process
            
        Returns:
            str: Generated URL or None if generation failed
        """
        # The prompt combines the extracted text with instructions for a short, simple domain
        prompt = (
            "Based on this text description, generate a short, simple, and memorable domain name that people might type directly: \n\n"
            f"{text}\n\n"
            "The domain name should be:\n"
            "1. Very short (preferably 3-6 characters)\n"
            "2. Easy to remember\n"
            "3. Similar to popular domains like 'chat.com', 'cool.com', or 'go.com'\n"
            "4. Have broad appeal and be intuitive\n"
            "5. Be the kind of domain name that would be valuable and expensive\n\n"
            "Only respond with the domain name itself and make sure it does NOT include '.com' or any other explanation."
        )
        
        try:
            # Call the Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You generate only short, valuable domain names based on the text provided. Be consistent and practical."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=10,  # Very short response
                top_p=0.95,
                stream=False
            )
            
            # Extract the URL from the response
            domain = response.choices[0].message.content.strip()
            
            # Clean up the response - remove any http/https prefix, .com suffix and any trailing paths
            import re
            domain = re.sub(r'^https?://', '', domain)  # Remove http:// or https://
            domain = re.sub(r'\.com$|\.org$|\.net$|\.io$', '', domain)  # Remove common TLDs
            domain = re.sub(r'/.*$', '', domain)  # Remove anything after the domain
            domain = domain.lower().strip()  # Lowercase and trim whitespace
            
            # Print the domain name prominently
            print("\n" + "=" * 50)
            print(f"GENERATED DOMAIN NAME: {domain}")
            print("=" * 50 + "\n")
            
            return domain
            
        except Exception as e:
            print(f"Error generating domain with Groq: {e}")
            return None
    
    def save_url_to_file(self, url: str, filename: str) -> bool:
        """
        Save the generated URL to a file
        
        Args:
            url: The URL to save
            filename: Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(filename)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            # Write URL to file
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(url)
                
            print(f"Successfully saved domain name to {filename}")
            return True
        except Exception as e:
            print(f"Failed to save domain name to file: {e}")
            return False
