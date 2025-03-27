"""
This module handles interactions with the Groq API
"""
import os
import json
import random
from typing import Optional, List
import groq

class GroqProcessor:
    """Handles text processing using Groq API"""
    
    def __init__(self, api_key: str, model: str):
        """Initialize the Groq API client"""
        self.client = groq.Groq(api_key=api_key)
        self.model = model
        # Track previously generated domains to avoid duplicates
        self.previous_domains = set()
        
        # Simpler, more focused prompts for generating content-relevant domains
        self.prompt_variations = [
            "Generate a simple English word that relates to this content",
            "What's a short, common word that captures the main idea here?",
            "Pick a basic, everyday English word that represents this concept",
            "Suggest a simple domain name based on this content",
            "What short English word best summarizes this?"
        ]
    
    def generate_url(self, text: str, custom_prompt: str = None) -> Optional[str]:
        """
        Generate a short, simple, memorable URL based on the given text
        
        Args:
            text: Text to base domain name on
            custom_prompt: Optional custom prompt to use instead of default
            
        Returns:
            str: Generated domain name without TLD (e.g. 'example' for 'example.com')
        """
        # Use a higher temperature for more variety
        temperature = random.uniform(0.7, 0.85)
        
        if custom_prompt:
            # Use the custom prompt if provided, injecting the text content
            prompt = custom_prompt.replace("{TEXT}", text[:300] if "{TEXT}" in custom_prompt else text[:300])
            
            # If the prompt doesn't include explicit formatting instructions, add them
            if "ONLY respond with" not in prompt and "Format your response" not in prompt:
                prompt += "\n\nONLY respond with the domain name itself, with no explanation or commentary."
        else:
            # Choose a prompt variation
            prompt_prefix = random.choice(self.prompt_variations)
            
            # Add an explicit instruction to generate something different if we have previous domains
            different_instruction = ""
            if self.previous_domains:
                different_instruction = f"Avoid these already used names: {', '.join(list(self.previous_domains)[:10])}. "
            
            # Improved prompt that focuses on content-relevant domain names with variable length
            prompt = (
                f"{prompt_prefix}. {different_instruction}\n\n"
                f"Content description:\n{text[:300]}...\n\n"
                "Requirements for the domain name:\n"
                "1. Must be a SINGLE word (real or invented)\n"
                "2. Between 3-12 characters long\n"
                "3. Must be relevant to the content\n"
                "4. Easy to spell and pronounce\n"
                "5. Memorable and distinctive\n\n"
                "Examples of good domain formats: chat, mail, zoom, slack, docs, notion, eventbrite, dropbox\n\n"
                "ONLY respond with the ONE word domain name. NO extensions, NO explanations."
            )
        
        try:
            # Call the Groq API with appropriate temperature
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You create simple domain names related to the content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=20,
                top_p=0.7,
                frequency_penalty=0.5,
                presence_penalty=0.5,
                stream=False
            )
            
            # Extract the domain from the response
            domain = response.choices[0].message.content.strip()
            
            # Clean up the response
            import re
            domain = re.sub(r'^https?://', '', domain)  # Remove http:// or https://
            domain = re.sub(r'\.com$|\.org$|\.net$|\.io$|\.app$|\.ai$', '', domain)  # Remove any TLDs
            domain = re.sub(r'/.*$', '', domain)  # Remove anything after the domain
            domain = re.sub(r'[^\w\-]', '', domain)  # Remove any non-alphanumeric characters except hyphens
            domain = domain.lower().strip()  # Lowercase and trim whitespace
            
            # If domain is empty or too short after cleaning, try again with a different prompt
            if not domain or len(domain) < 3:
                print("Generated domain was too short, trying again...")
                # Recursive call with a more specific prompt
                return self.generate_url("Generate a simple word for: " + text[:100])
                
            # Add to our set of previous domains to avoid duplicates in future calls
            self.previous_domains.add(domain)
            
            # Print the domain name prominently
            print("\n" + "=" * 50)
            print(f"GENERATED DOMAIN NAME: {domain} (temperature: {temperature:.2f})")
            print("=" * 50 + "\n")
            
            return domain
            
        except Exception as e:
            print(f"Error generating domain with Groq: {e}")
            # Generate a basic fallback if API call fails
            return "web" + str(random.randint(100, 999))
    
    def generate_alternative_domains(self, failed_domain: str, original_text: str = None, count: int = 20, custom_prompt: str = None) -> List[str]:
        """
        Generate a list of alternative domain names based on the original text.
        
        Args:
            failed_domain: The domain name that failed
            original_text: The original text content to base alternatives on
            count: Number of alternatives to generate (default: 20)
            custom_prompt: Optional custom prompt to use instead of default
            
        Returns:
            list: List of alternative domain names
        """
        print(f"Generating {count} alternatives based on original content...")
        
        # Generate a batch of related domain names
        domains = []
        temperature = 0.9  # Higher temperature for more variety in alternatives
        
        if custom_prompt:
            # Use the custom prompt if provided, injecting the failed domain and text content
            prompt = custom_prompt
            prompt = prompt.replace("{FAILED_DOMAIN}", failed_domain)
            prompt = prompt.replace("{TEXT}", original_text[:400] if original_text and "{TEXT}" in prompt else "")
            prompt = prompt.replace("{COUNT}", str(count))
            
            # If the prompt doesn't include explicit formatting instructions, add them
            if "Format your response" not in prompt:
                prompt += (
                    f"\n\nFormat your response as a simple list of {count} domain names, "
                    "each on a separate line, with no explanations or numbering."
                )
        else:
            if original_text:
                # Extract key topics from the text first to focus the domain generation
                key_topics = self._extract_key_topics(original_text)
                text_to_use = original_text[:400]  # Shorter text to focus on main content
                
                # Create a more focused prompt that emphasizes relevance to the content
                prompt = (
                    f"The domain name '{failed_domain}' was already taken. Generate {count} highly relevant "
                    f"alternative domain names directly related to this content:\n\n"
                    f"\"{text_to_use}\"\n\n"
                    f"Key topics identified in this content: {key_topics}\n\n"
                    "Requirements for each domain name:\n"
                    "1. Single words directly related to the content\n"
                    "2. Mix of short (3-6 characters) and longer (7-12 characters) names\n"
                    "3. Must strongly connect to the main topic or purpose of the content\n"
                    "4. Easy to spell and remember\n"
                    "5. Focus on words that capture what the website actually does or offers\n"
                    "6. Each name should reflect a different aspect of the content\n\n"
                    "Format your response as a numbered list, with each item being only the domain name:\n"
                    "1. chat\n2. mail\n3. web\n... and so on."
                )
            else:
                prompt = (
                    f"The domain name '{failed_domain}' was already taken. Generate {count} alternative "
                    "domain names that are simple English words or made-up terms.\n\n"
                    "Requirements for each domain name:\n"
                    "1. Mix of short (3-6 chars) and longer (7-12 chars) names\n"
                    "2. Easy to spell and remember\n"
                    "3. Related to the concept suggested by '{failed_domain}'\n\n"
                    "Format your response as a numbered list, with each item being only the domain name:\n"
                    "1. chat\n2. mail\n3. web\n... and so on."
                )
        
        try:
            # Call the API with modified parameters for more relevant results
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You generate diverse domain names with a mix of lengths (short to medium-long)."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=250,
                top_p=0.9,
                frequency_penalty=0.6,
                presence_penalty=0.6,
                stream=False
            )
            
            # Process the response
            response_text = response.choices[0].message.content.strip()
            
            # Parse the list - look for numbered items or separate entries
            import re
            
            # Try to find entries with "1. domain" pattern first
            numbered_items = re.findall(r'\d+[\.\)]\s*([a-zA-Z0-9\-]+)', response_text)
            if numbered_items:
                for domain in numbered_items:
                    clean_domain = domain.strip().lower()
                    # Basic validation
                    if clean_domain and len(clean_domain) >= 3 and clean_domain != failed_domain:
                        domains.append(clean_domain)
                        self.previous_domains.add(clean_domain)
            else:
                # Fall back to splitting on newlines or commas
                for item in re.split(r'[\n,]', response_text):
                    # Clean and extract domain name, ignoring numbers/bullets
                    clean_domain = re.sub(r'^\d+[\.\)]?\s*', '', item).strip().lower()
                    clean_domain = re.sub(r'[^\w\-]', '', clean_domain)
                    
                    if clean_domain and len(clean_domain) >= 3 and clean_domain != failed_domain:
                        domains.append(clean_domain)
                        self.previous_domains.add(clean_domain)
            
            # If we didn't get enough domains, try another approach with topic extraction
            if len(domains) < count and original_text:
                # Second attempt with more topic-focused approach
                second_prompt = (
                    f"Based on this text:\n\n\"{original_text[:300]}\"\n\n"
                    f"What are {count - len(domains)} words that best describe "
                    f"the core purpose, functionality, or main topic of this website? "
                    f"Mix of short (3-6 letters) and longer (7-12 letters) names. "
                    f"Focus on words that would make good domain names directly related to what this service actually does.\n"
                    f"Just list the words one per line, no explanations."
                )
                
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You generate very short domain names."},
                        {"role": "user", "content": second_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=100,
                    stream=False
                )
                
                second_text = second_response.choices[0].message.content.strip()
                
                # Process each line
                for line in second_text.split('\n'):
                    word = line.strip().lower()
                    word = re.sub(r'[^\w\-]', '', word)
                    
                    if word and len(word) >= 3 and word not in domains and word != failed_domain:
                        domains.append(word)
                        self.previous_domains.add(word)
                        
                        if len(domains) >= count:
                            break
        
        except Exception as e:
            print(f"Error generating alternative domains: {e}")
        
        # If we still don't have enough domains, add some basic generic ones
        if len(domains) < count:
            generic_domains = [
                'web', 'app', 'site', 'page', 'link', 'net', 'hub', 'spot', 'zone', 'home',
                'go', 'get', 'try', 'use', 'view', 'find', 'info', 'help', 'talk', 'meet'
            ]
            needed = count - len(domains)
            for i in range(min(needed, len(generic_domains))):
                word = generic_domains[i]
                if word not in domains and word != failed_domain:
                    domains.append(word)
        
        # Limit to the requested count
        domains = domains[:count]
        
        # Print the list of alternatives
        print("\n" + "=" * 50)
        print(f"ALTERNATIVE DOMAIN NAMES FOR '{failed_domain}':")
        for i, domain in enumerate(domains, 1):
            print(f"{i}. {domain}")
        print("=" * 50 + "\n")
        
        return domains
    
    def _extract_key_topics(self, text: str) -> str:
        """
        Extract key topics from the text to help focus domain name generation.
        
        Args:
            text: The text to extract topics from
            
        Returns:
            str: Comma-separated list of key topics
        """
        try:
            # Use Groq to extract key topics from the content
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You identify the core topics and purpose of content."},
                    {"role": "user", "content": f"From this text, identify 5-7 key topics or themes that represent what this website/app is about. Respond with ONLY the topics as a comma-separated list of single words or short phrases:\n\n{text[:500]}"}
                ],
                temperature=0.1,
                max_tokens=50,
                stream=False
            )
            
            topics = response.choices[0].message.content.strip()
            print(f"Extracted key topics: {topics}")
            return topics
            
        except Exception as e:
            print(f"Error extracting topics: {e}")
            return "website, application, service, platform, tool"
    
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
