"""
Integration script that scans handwritten images using OpenAI Vision API
and inserts the extracted bulleted list into Notion.
"""
import base64
from datetime import datetime
from openai import OpenAI
from cost_calculator import ImageAnalysisCostCalculator
from experiments.notion_example import create_page_with_bulleted_list

# Initialize OpenAI client
client = OpenAI()


def encode_image(image_path):
    """Encode image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def scan_image_to_text(image_path, prompt_path="prompt.txt"):
    """
    Scan an image using OpenAI Vision API and extract text as bulleted list.
    
    Args:
        image_path: Path to the image file
        prompt_path: Path to the prompt file (default: "prompt.txt")
    
    Returns:
        Extracted text as string (bulleted list format)
    """
    # Read prompt from file
    with open(prompt_path, "r", encoding="utf-8") as prompt_file:
        prompt_text = prompt_file.read().strip()
    
    # Calculate cost before making the API call
    cost_calculator = ImageAnalysisCostCalculator(model="gpt-4.1", tier="standard")
    cost_info = cost_calculator.calculate_cost_both(image_path=image_path, detail="high")
    print(f"Estimated cost for this image:")
    print(f"  Tokens: {cost_info['tokens']:,}")
    print(f"  Dollars: ${cost_info['dollars']:.6f}")
    print(f"  Model: {cost_info['model']} ({cost_info['tier']} tier)")
    print()
    
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


def scan_and_insert_to_notion(image_path, prompt_path="prompt.txt"):
    """
    Complete workflow: Scan image and insert result into Notion.
    
    Args:
        image_path: Path to the image file to scan
        prompt_path: Path to the prompt file (default: "prompt.txt")
    
    Returns:
        Notion page creation response
    """
    print(f"Processing image: {image_path}")
    print("-" * 50)
    
    # Step 1: Scan image and extract text
    bulleted_text = scan_image_to_text(image_path, prompt_path)
    
    # Step 2: Format title with current datetime
    page_title = format_datetime_title()
    
    # Step 3: Insert into Notion
    print(f"Creating Notion page: {page_title}")
    print("Inserting bulleted list into Notion...")
    
    try:
        result = create_page_with_bulleted_list(page_title, bulleted_text)
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

