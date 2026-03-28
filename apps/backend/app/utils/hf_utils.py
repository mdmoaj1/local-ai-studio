import re

def parse_hf_repo_id(input_str: str) -> str:
    """Parse a Hugging Face repo ID from a string or a full URL.
    
    Examples:
    - "Qwen/Qwen3-0.6B" -> "Qwen/Qwen3-0.6B"
    - "https://huggingface.co/Qwen/Qwen3-0.6B" -> "Qwen/Qwen3-0.6B"
    - "huggingface.co/Qwen/Qwen3-0.6B" -> "Qwen/Qwen3-0.6B"
    - "https://huggingface.co/Qwen/Qwen3-0.6B/tree/main" -> "Qwen/Qwen3-0.6B"
    """
    input_str = input_str.strip()
    
    # Remove protocol
    input_str = re.sub(r'^https?://', '', input_str)
    
    # Check if starts with huggingface.co
    if input_str.startswith('huggingface.co/'):
        input_str = input_str[len('huggingface.co/'):]
    
    # Split by / and take first two parts (org/repo)
    parts = input_str.split('/')
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
        
    return input_str
