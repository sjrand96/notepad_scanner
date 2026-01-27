"""
Integration script that scans handwritten images using OpenAI Vision API
and inserts the extracted bulleted list into Notion.
"""
import base64
import os
from datetime import datetime
from openai import OpenAI
from backend.notion_client import create_page_with_bulleted_list
from backend.user_manager import get_user

# Initialize OpenAI client
client = OpenAI()


def encode_image(image_path):
    """Encode image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def scan_image_to_text(image_path, prompt_path="backend/prompts/handwriting_ocr.txt"):
    """
    Scan an image using OpenAI Vision API and extract text as bulleted list.
    
    Args:
        image_path: Path to the image file
        prompt_path: Path to the prompt file (default: "backend/prompts/handwriting_ocr.txt")
    
    Returns:
        Extracted text as string (bulleted list format)
    """
    # Read prompt from file
    with open(prompt_path, "r", encoding="utf-8") as prompt_file:
        prompt_text = prompt_file.read().strip()
    
    # Encode image to base64
    base64_image = encode_image(image_path)
    
    # Call OpenAI Vision API
    print("Scanning image with OpenAI Vision API...")
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
    
    extracted_text = response.output_text
    print("✓ Image scanned successfully")
    print()
    
    return extracted_text


def format_datetime_title():
    """
    Format current datetime as 'Scan MM/DD/YYYY HH:MM:SS'.
    
    Returns:
        Formatted datetime string
    """
    now = datetime.now()
    return now.strftime("Scan %m/%d/%Y %H:%M:%S")


def scan_and_insert_to_notion(image_path, prompt_path="backend/prompts/handwriting_ocr.txt", user_id=None):
    """
    Complete workflow: Scan image and insert result into Notion with the image attached.
    
    Args:
        image_path: Path to the image file to scan
        prompt_path: Path to the prompt file (default: "backend/prompts/handwriting_ocr.txt")
        user_id: User ID to use for Notion credentials (e.g., "spencer", "celeste")
                If not provided, uses environment variable or defaults to Spencer
    
    Returns:
        Notion page creation response
    """
    print(f"Processing image: {image_path}")
    print("-" * 50)
    
    # Get user credentials
    if user_id:
        user = get_user(user_id)
        if not user:
            raise ValueError(f"User '{user_id}' not found")
        database_id = user.get("notion_database_id")
        notion_token = user.get("notion_token")
        print(f"Using credentials for user: {user.get('name', user_id)}")
    else:
        # Fall back to environment variables or defaults
        database_id = os.getenv("NOTION_DATABASE_ID", "2c1cf28f26d0803eb293cae3ff414acc")
        notion_token = None  # Will use default from config
        print("Using default credentials from environment")
    
    if not database_id:
        raise ValueError("Notion database ID not configured")
    if user_id and not notion_token:
        raise ValueError(f"Notion token not configured for user {user_id}")
    
    # Step 1: Scan image and extract text
    bulleted_text = scan_image_to_text(image_path, prompt_path)
    
    # Step 2: Format title with current datetime
    page_title = format_datetime_title()
    
    # Step 3: Insert into Notion with image
    print(f"Creating Notion page: {page_title}")
    print("Inserting bulleted list and image into Notion...")
    
    try:
        result = create_page_with_bulleted_list(
            database_id=database_id,
            title=page_title,
            bulleted_text=bulleted_text,
            notion_token=notion_token,
            image_path=image_path
        )
        print(f"✓ Successfully created Notion page with ID: {result['id']}")
        print(f"  Page URL: https://www.notion.so/{result['id'].replace('-', '')}")
        return result
    except Exception as e:
        print(f"✗ Error creating Notion page: {str(e)}")
        raise


if __name__ == "__main__":
    # Default image path - can be modified or passed as argument
    image_path = "images/IMG_7712.JPG"
    
    # Run the complete workflow
    result = scan_and_insert_to_notion(image_path)
    print()
    print("=" * 50)
    print("Integration test completed successfully!")

