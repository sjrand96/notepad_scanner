"""
OpenAI Vision API client for scanning images.
"""
import base64
from openai import OpenAI
from backend.config import OPENAI_API_KEY, PROMPT_PATH


client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def encode_image(image_path):
    """Encode image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def scan_image_to_text(image_path, prompt_path=None):
    """
    Scan an image using OpenAI Vision API and extract text as bulleted list.
    
    Args:
        image_path: Path to the image file
        prompt_path: Path to the prompt file (default: PROMPT_PATH)
    
    Returns:
        Extracted text as string (bulleted list format)
    """
    if prompt_path is None:
        prompt_path = PROMPT_PATH
    
    if client is None:
        raise ValueError("OpenAI API key not configured")
    
    with open(prompt_path, "r", encoding="utf-8") as prompt_file:
        prompt_text = prompt_file.read().strip()
    
    base64_image = encode_image(image_path)
    
    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    { "type": "input_text", "text": prompt_text },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "high"
                    },
                ],
            }
        ],
    )
    
    return response.output_text
