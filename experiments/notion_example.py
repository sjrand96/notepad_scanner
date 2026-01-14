import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",  # use a current version from Notion docs
    "Content-Type": "application/json",
}

def parse_markdown_to_notion_blocks(markdown_text: str):
    """
    Parse markdown-style text (headers and bulleted lists) into Notion API block format.
    
    Supports:
    - Headers: ### Header text (converted to heading_3)
    - Bulleted lists with proper nesting (up to 3 levels)
    
    Nested bullets are placed in the 'children' array of their parent bulleted_list_item.
    Notion supports up to 3 levels of nesting.
    
    Args:
        markdown_text: String containing markdown-style content (headers and bullets)
    
    Returns:
        List of top-level Notion block objects (with nested children properly structured)
    """
    lines = markdown_text.strip().split('\n')
    top_level_blocks = []
    
    # Stack to track parent bullet blocks at each indentation level
    # Each element is (indent_level, block)
    parent_stack = []
    
    for line in lines:
        line = line.rstrip()
        if not line.strip():
            continue
        
        # Check if this is a header (starts with ###)
        if line.strip().startswith('###'):
            # Clear the parent stack when we hit a header (headers break bullet nesting)
            parent_stack = []
            
            # Extract header text (remove ### and any leading/trailing spaces)
            header_text = line.strip()[3:].strip()
            
            if header_text:
                # Create heading_3 block
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
        
        # Process as bullet point
        # Count leading spaces to determine indentation level
        original_indent = len(line) - len(line.lstrip())
        
        # Normalize: treat 0-1 spaces as level 0, 2-3 as level 1, 4-5 as level 2, etc.
        indent_level = original_indent // 2
        
        # Cap at 3 levels (Notion's maximum)
        if indent_level > 3:
            indent_level = 3
        
        # Remove leading spaces and bullet marker
        content = line.lstrip('- ').lstrip('* ').strip()
        
        if not content:
            continue
        
        # Create bulleted_list_item block
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
        
        # Remove parents from stack that are at the same or deeper level
        while parent_stack and parent_stack[-1][0] >= indent_level:
            parent_stack.pop()
        
        if indent_level == 0:
            # Top-level item - add to top_level_blocks
            top_level_blocks.append(block)
            parent_stack = [(0, block)]
        else:
            # Nested item - add to parent's children
            if parent_stack:
                parent_indent, parent_block = parent_stack[-1]
                
                # Initialize children array if it doesn't exist
                if "children" not in parent_block["bulleted_list_item"]:
                    parent_block["bulleted_list_item"]["children"] = []
                
                # Add this block as a child of the parent
                parent_block["bulleted_list_item"]["children"].append(block)
                
                # Add this block to the stack as a potential parent
                parent_stack.append((indent_level, block))
            else:
                # No parent found, treat as top-level (shouldn't happen with proper formatting)
                top_level_blocks.append(block)
                parent_stack = [(indent_level, block)]
    
    return top_level_blocks


def create_page_in_database(title: str, notes: str):
    url = "https://api.notion.com/v1/pages"
    
    payload = {
        "parent": { "database_id": DATABASE_ID },
        "properties": {
            "Name": {  # must match your Notion database's title property name
                "title": [
                    {
                        "text": { "content": title }
                    }
                ]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        { "type": "text", "text": { "content": notes } }
                    ]
                }
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def create_page_with_bulleted_list(title: str, bulleted_text: str):
    """
    Create a Notion page with headers and bulleted lists.
    
    Args:
        title: Title for the page
        bulleted_text: Markdown-style text (can include headers ### and bullets)
    
    Returns:
        Response JSON from Notion API
    """
    url = "https://api.notion.com/v1/pages"
    
    # Parse markdown text (headers and bullets) into Notion blocks
    children = parse_markdown_to_notion_blocks(bulleted_text)
    
    payload = {
        "parent": { "database_id": DATABASE_ID },
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

if __name__ == "__main__":
    page = create_page_in_database(
        title="Example row from Python",
        notes="Hello from my Python script!"
    )
    print("Created page with id:", page["id"])