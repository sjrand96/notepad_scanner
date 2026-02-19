# Image Upload Implementation

## Summary
Successfully implemented Notion's Direct Upload method to attach scanned images to created Notion pages. Images are now automatically uploaded and displayed at the top of each scanned page.

## Implementation Details

### 3-Step Upload Process
Following Notion's documentation, the implementation uses:

1. **Create File Upload Object** - Request a file upload ID from Notion
2. **Upload File Content** - Send the binary image data via multipart/form-data
3. **Attach to Page** - Include the file_upload_id in the page creation payload

### Files Modified

#### 1. `backend/notion_client.py`
- Added `upload_image_to_notion()` function to handle the upload process
- Updated `create_page_with_bulleted_list()` to accept optional `image_path` parameter
- When an image is provided, it's uploaded and prepended as an image block

#### 2. `backend/config.py`
- Updated `NOTION_TOKEN` to use `SPENCER_NOTION_TOKEN` environment variable

#### 3. `scan_to_notion.py`
- Changed import from `experiments.notion_example` to `backend.notion_client`
- Updated function call to pass `image_path` parameter
- Now uploads both the extracted text and the original scanned image

#### 4. `experiments/notion_example.py`
- Updated function signature to match new API (for backward compatibility)
- Added warning that image upload requires backend.notion_client

### Integration Points

The image upload functionality automatically works with:
- **Direct scanning**: `scan_to_notion.py` - scan an image and create Notion page
- **App workflow**: Capture frames, crop to fixed ROI, scan, and upload to Notion

### Testing

Successfully tested with:
1. Simple image upload to Notion (verified Direct Upload method works)
2. Image + text upload (verified integration with bulleted list parsing)
3. Full OpenAI Vision scan + image upload (verified end-to-end workflow)

### Example Usage

```python
from backend.notion_client import create_page_with_bulleted_list

# Create page with text and image
result = create_page_with_bulleted_list(
    database_id="your-database-id",
    title="My Scanned Notes",
    bulleted_text="### Notes\\n- First bullet\\n- Second bullet",
    image_path="path/to/image.jpg"
)
```

### Technical Notes

- Supports common image formats: JPEG, PNG, GIF, WebP
- File size limit: 20 MB (as per Notion API constraints)
- Uploaded images become permanent once attached to a page
- Images appear at the top of the page, before the extracted text
- Content type is automatically detected from file extension

### User Management

The system now supports multiple users with their own Notion credentials:

#### Environment Variables Required

- `SPENCER_NOTION_TOKEN` - Spencer's Notion API token
- `SPENCER_NOTION_DATABASE_ID` - Spencer's Notion database ID
- `CELESTE_NOTION_TOKEN` - Celeste's Notion API token
- `CELESTE_NOTION_DATABASE_ID` - Celeste's Notion database ID

#### User Selection

**Standalone Scripts:**
- `scan_to_notion.py` - Pass `user_id` parameter: `scan_and_insert_to_notion(image_path, user_id='spencer')`
- `capture_scan_to_notion.py` - Prompts for user selection at startup

**Web API:**
- Automatically uses the selected user's credentials from the session

User credentials are managed in `data/users.json` and loaded from environment variables by `backend/user_manager.py`.

## Next Steps

The basic implementation is complete and working. Future enhancements could include:
- Support for multiple images per page
- Image optimization/compression before upload
- Error handling for network failures with retry logic
- Support for files larger than 20 MB using multi-part upload
