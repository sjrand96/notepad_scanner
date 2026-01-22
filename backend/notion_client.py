"""
Notion API client for creating pages with bulleted lists and image uploads.
"""
import requests
import os
from backend.config import NOTION_TOKEN, NOTION_API_URL

NOTION_VERSION = "2022-06-28"


def parse_markdown_to_notion_blocks(markdown_text):
    """
    Parse markdown-style text (headers and bulleted lists) into Notion API block format.
    
    Supports:
    - Headers: ### Header text (converted to heading_3)
    - Bulleted lists with proper nesting (up to 3 levels)
    
    Args:
        markdown_text: String containing markdown-style content (headers and bullets)
    
    Returns:
        List of top-level Notion block objects (with nested children properly structured)
    """
    lines = markdown_text.strip().split('\n')
    top_level_blocks = []
    parent_stack = []
    
    for line in lines:
        line = line.rstrip()
        if not line.strip():
            continue
        
        if line.strip().startswith('###'):
            parent_stack = []
            header_text = line.strip()[3:].strip()
            
            if header_text:
                header_block = {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": { "content": header_text }
                            }
                        ]
                    }
                }
                top_level_blocks.append(header_block)
            continue
        
        original_indent = len(line) - len(line.lstrip())
        indent_level = original_indent // 2
        if indent_level > 3:
            indent_level = 3
        
        content = line.lstrip('- ').lstrip('* ').strip()
        if not content:
            continue
        
        block = {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": { "content": content }
                    }
                ]
            }
        }
        
        while parent_stack and parent_stack[-1][0] >= indent_level:
            parent_stack.pop()
        
        if indent_level == 0:
            top_level_blocks.append(block)
            parent_stack = [(0, block)]
        else:
            if parent_stack:
                parent_indent, parent_block = parent_stack[-1]
                
                if "children" not in parent_block["bulleted_list_item"]:
                    parent_block["bulleted_list_item"]["children"] = []
                
                parent_block["bulleted_list_item"]["children"].append(block)
                parent_stack.append((indent_level, block))
            else:
                top_level_blocks.append(block)
                parent_stack = [(indent_level, block)]
    
    return top_level_blocks


def upload_image_to_notion(image_path, notion_token=None):
    """
    Upload an image file to Notion using the Direct Upload method.
    
    This implements the 3-step process:
    1. Create a File Upload object
    2. Upload file contents
    3. Return the file_upload_id for attaching to blocks
    
    Args:
        image_path: Path to the image file
        notion_token: Notion API token (optional, uses NOTION_TOKEN from config if not provided)
    
    Returns:
        file_upload_id: The ID to use when attaching the image to blocks
    """
    token = notion_token or NOTION_TOKEN
    if not token:
        raise ValueError("Notion token not provided and NOTION_TOKEN environment variable not set")
    
    # Determine content type from file extension
    filename = os.path.basename(image_path)
    file_ext = os.path.splitext(filename)[1].lower()
    content_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    content_type = content_type_map.get(file_ext, "image/jpeg")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    # Step 1: Create file upload object
    create_url = f"{NOTION_API_URL}/file_uploads"
    payload = {
        "filename": filename,
        "content_type": content_type
    }
    
    response = requests.post(create_url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(
            f"File creation failed with status code {response.status_code}: {response.text}"
        )
    
    file_upload = response.json()
    file_upload_id = file_upload['id']
    
    # Step 2: Upload file content
    upload_url = f"{NOTION_API_URL}/file_uploads/{file_upload_id}/send"
    upload_headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION
    }
    
    with open(image_path, "rb") as f:
        files = {
            "file": (filename, f, content_type)
        }
        response = requests.post(upload_url, headers=upload_headers, files=files)
    
    if response.status_code != 200:
        raise Exception(
            f"File upload failed with status code {response.status_code}: {response.text}"
        )
    
    return file_upload_id


def create_page_with_bulleted_list(database_id, title, bulleted_text, notion_token=None, image_path=None):
    """
    Create a Notion page with headers and bulleted lists, optionally with an image.
    
    Args:
        database_id: Notion database ID
        title: Title for the page
        bulleted_text: Markdown-style text (can include headers ### and bullets)
        notion_token: Notion API token (optional, uses NOTION_TOKEN from config if not provided)
        image_path: Optional path to an image file to include at the end of the page
    
    Returns:
        Response JSON from Notion API
    """
    token = notion_token or NOTION_TOKEN
    if not token:
        raise ValueError("Notion token not provided and NOTION_TOKEN environment variable not set")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    
    children = parse_markdown_to_notion_blocks(bulleted_text)
    
    # If an image is provided, upload it and append an image block with header
    if image_path and os.path.exists(image_path):
        print(f"Uploading image to Notion: {os.path.basename(image_path)}")
        file_upload_id = upload_image_to_notion(image_path, token)
        
        # Create "Source Photo:" header block (heading_2)
        header_block = {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": { "content": "Source Photo:" }
                    }
                ]
            }
        }
        
        # Create image block
        image_block = {
            "object": "block",
            "type": "image",
            "image": {
                "type": "file_upload",
                "file_upload": {
                    "id": file_upload_id
                }
            }
        }
        
        # Append header and image blocks to children
        children = children + [header_block, image_block]
        print(f"✓ Image uploaded and attached to page")
    
    url = f"{NOTION_API_URL}/pages"
    
    payload = {
        "parent": { "database_id": database_id },
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": { "content": title }
                    }
                ]
            }
        },
        "children": children
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
