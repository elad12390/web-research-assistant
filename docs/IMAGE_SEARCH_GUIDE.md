# Stock Image Search Guide

## Overview

The `search_images` tool provides access to high-quality, royalty-free stock images from Pixabay. Perfect for finding photos, illustrations, and vector graphics for projects, presentations, or design work.

## Setup

### 1. Get a Free Pixabay API Key

1. Visit [pixabay.com/api/docs](https://pixabay.com/api/docs/)
2. Sign up for a free account (if you don't have one)
3. Navigate to the API documentation page
4. Copy your API key

### 2. Configure the API Key

**Option A: Environment Variable (Recommended)**
```bash
export PIXABAY_API_KEY="your-api-key-here"
```

**Option B: MCP Server Configuration**

For Claude Desktop, add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "web-research-assistant": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/searxng-mcp",
        "run",
        "searxng-mcp"
      ],
      "env": {
        "PIXABAY_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

For OpenCode, add to your `opencode.json`:
```json
{
  "mcpServers": {
    "web-research-assistant": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/searxng-mcp",
        "run",
        "searxng-mcp"
      ],
      "env": {
        "PIXABAY_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### 3. Restart the MCP Server

After configuring the API key, restart your MCP client (Claude Desktop or OpenCode).

## Usage Examples

### Basic Search
```python
search_images("mountain landscape")
```

### Photo Search
```python
search_images(
    query="sunset beach",
    image_type="photo",
    orientation="horizontal"
)
```

### Illustration Search
```python
search_images(
    query="business icons",
    image_type="illustration",
    max_results=5
)
```

### Vector Graphics
```python
search_images(
    query="technology logo",
    image_type="vector",
    orientation="horizontal"
)
```

### Vertical Images
```python
search_images(
    query="smartphone mockup",
    orientation="vertical",
    max_results=15
)
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | _required_ | Search term (e.g., "sunset beach", "office workspace") |
| `reasoning` | string | "Stock image search" | Why you're searching (for analytics) |
| `image_type` | string | "all" | Type: "all", "photo", "illustration", "vector" |
| `orientation` | string | "all" | Orientation: "all", "horizontal", "vertical" |
| `max_results` | int | 10 | Number of results (1-20) |

## Image Types

### Photo
Real photographs from photographers around the world. Best for:
- Realistic scenes and objects
- People and portraits
- Nature and landscapes
- Product photography

### Illustration
Digital illustrations and artwork. Best for:
- Stylized graphics
- Concept art
- Editorial illustrations
- Creative designs

### Vector
Scalable vector graphics (SVG). Best for:
- Logos and icons
- Infographics
- Print materials
- Web design elements

## Response Format

Each image result includes:
- **Tags**: Descriptive keywords
- **Resolution**: Width x Height in pixels
- **Stats**: Views, downloads, and likes
- **Creator**: Username of the photographer/artist
- **URLs**:
  - `Preview`: Small thumbnail (150px)
  - `Large`: High-resolution version (1280px)
  - `Full HD`: Full resolution (when available)

### Example Output

```
Stock Images for: sunset beach
Type: Photo | Orientation: Horizontal | Found: 3 images
──────────────────────────────────────────────────────────────────────

1. sunset, beach, sea, ocean, summer, water, nature, landscape
   Resolution: 5184x3456 | 👁️ 76,871 | ⬇️ 60,754 | ❤️ 263
   By: photographer_name
   Preview: https://cdn.pixabay.com/.../sunset-5383043_150.jpg
   Large: https://pixabay.com/get/.../sunset_1280.jpg
   Full HD: https://pixabay.com/get/.../sunset_fullhd.jpg
```

## No API Key Configured

If you try to use `search_images` without configuring an API key, you'll see:

```
⚠️ Pixabay API key not configured

To use image search, you need to configure your Pixabay API key.

Steps:
1. Get a free API key from: https://pixabay.com/api/docs/
2. Set the environment variable: PIXABAY_API_KEY=your_key_here
3. Restart the MCP server

You can set it in your shell:
  export PIXABAY_API_KEY='your_key_here'

Or add it to your MCP server configuration.
```

## Best Practices

### 1. Be Specific
✅ Good: "modern office workspace"  
❌ Too broad: "office"

### 2. Use Multiple Keywords
✅ Good: "sunset ocean waves beach"  
❌ Too limited: "sunset"

### 3. Choose the Right Type
- Need a photo? → `image_type="photo"`
- Need an icon? → `image_type="vector"`
- Need artwork? → `image_type="illustration"`

### 4. Consider Orientation
- Website headers → `orientation="horizontal"`
- Mobile screens → `orientation="vertical"`
- Flexible layout → `orientation="all"`

### 5. Adjust Result Count
- Quick browse → `max_results=5`
- Comprehensive search → `max_results=20`

## Common Use Cases

### Blog Post Header
```python
search_images(
    query="technology abstract blue",
    image_type="photo",
    orientation="horizontal",
    max_results=5
)
```

### Presentation Slide
```python
search_images(
    query="teamwork collaboration",
    image_type="photo",
    orientation="horizontal",
    max_results=10
)
```

### App Icon
```python
search_images(
    query="mobile app icon",
    image_type="vector",
    max_results=15
)
```

### Social Media Post
```python
search_images(
    query="motivational quote background",
    orientation="vertical",
    max_results=8
)
```

## Rate Limits

Pixabay's free tier includes:
- 5,000 requests per hour
- 100 requests per minute

The tool automatically handles rate limit errors with a helpful message.

## License Information

All images from Pixabay are released under the Pixabay License:
- Free to use for commercial and non-commercial purposes
- No attribution required (but appreciated)
- Modifications allowed
- Cannot be resold or redistributed as-is

Always check the [Pixabay License](https://pixabay.com/service/license/) for the most current terms.

## Troubleshooting

### "API key not configured"
→ Set the `PIXABAY_API_KEY` environment variable and restart the server

### "Rate limit exceeded"
→ Wait a moment and try again. You may have exceeded the hourly/minute limit.

### "No images found"
→ Try broader search terms or different image type/orientation filters

### HTTP 400 Error
→ Check your search parameters. The query might be invalid or too complex.

---

**Tool:** `search_images`  
**API:** Pixabay API v1  
**Added:** November 15, 2025  
**Status:** Production Ready ✅
