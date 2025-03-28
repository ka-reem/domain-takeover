# Custom AI Prompts for Domain Name Generation

This document explains how to use custom AI prompts with the domain takeover tool.

## Using Custom Prompts

You can provide custom AI prompts in two ways:

1. Directly on the command line using the `--prompt` option:
   ```bash
   python main.py --url "https://lovable.dev/projects/example" --prompt "Generate a catchy, professional domain name based on this content: {TEXT}"
   ```

2. From a file using the `--prompt-file` option:
   ```bash
   python main.py --url "https://lovable.dev/projects/example" --prompt-file "my_custom_prompt.txt"
   ```

## Placeholder Variables

In your custom prompts, you can use these special placeholders:
- `{TEXT}` - Will be replaced with the extracted content
- `{FAILED_DOMAIN}` - When generating alternatives, will be replaced with the domain name that failed
- `{COUNT}` - When generating alternatives, will be replaced with the number of alternatives to generate

## Example Custom Prompts

### Basic Domain Generation

```
Generate a domain name for a web application based on this content: {TEXT}

The domain should be:
1. Between 4-12 characters
2. Easy to spell and remember
3. Unique and catchy
4. Relevant to the content and purpose

Just provide a single word with no explanation.
```

### Alternative Domain Generation

```
The domain '{FAILED_DOMAIN}' was already taken. Create {COUNT} alternative domain names that:

1. Are relevant to this content: {TEXT}
2. Mix of short (3-6 chars) and longer (7-12 chars) names
3. Easy to remember and type
4. Unique and creative

Format as a simple list, one name per line, no explanations.
```

### Creative Naming Strategy

```
You are an expert domain name consultant. Create a perfect domain name for a new web app with this description: {TEXT}

The domain should:
1. Be memorable and distinctive
2. Contain 5-9 characters
3. Be easy to spell after hearing it spoken
4. Not use common words that are likely already registered
5. Capture the essence of what this application does

Just provide the domain name itself, no extensions or explanations.
```

## Tips for Writing Effective Prompts

1. **Be specific** about the length and style of domain names you want
2. **Mention the purpose** of the web application to get more relevant names
3. **Request variety** in the alternatives (short/long, made-up/real words, etc.)
4. **Ask for formatting** that's easy to parse (e.g., one name per line)
5. **Include explicit instructions** to avoid explanations or commentary

By customizing your prompts, you can better control the types of domain names generated.
