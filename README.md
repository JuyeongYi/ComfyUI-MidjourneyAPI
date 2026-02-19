# ComfyUI-MidJourney

ComfyUI custom nodes for Midjourney image generation via [midjourney-api](https://github.com/JuyeongYi/PythonMidjourneyAPIClient).

## Installation

1. Clone into `ComfyUI/custom_nodes/`:
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/JuyeongYi/ComfyUI-MidJourney.git
   ```

2. Install dependencies:
   ```bash
   pip install -r ComfyUI-MidJourney/requirements.txt
   ```

3. Set up authentication by placing a `.env` file in the **ComfyUI root** directory.
   See [PythonMidjourneyAPIClient](https://github.com/JuyeongYi/PythonMidjourneyAPIClient) for authentication details.

## Nodes

### Generation

| Node | Description | Outputs |
|------|-------------|---------|
| **MidJourney Imagine** | Text-to-image generation | 4 images + job_id |
| **MidJourney Vary** | Strong/Subtle variation | 4 images + job_id |
| **MidJourney Upscale** | 2x upscale (subtle/creative) | 1 image + job_id |
| **MidJourney Pan** | Directional image extension | 4 images + job_id |
| **MidJourney Download** | Download images by job ID | 4 images |

### Parameters

| Node | Description |
|------|-------------|
| **Imagine V7 Params** | V7 parameter configuration (aspect ratio, stylize, chaos, seed, quality, raw, tile, sref, oref, personalize, visibility, etc.) |
| **Save Imagine Params** | Save parameters as JSON preset |
| **Load Imagine Params** | Load parameters from JSON preset |

### Utilities

| Node | Description |
|------|-------------|
| **Common Resolution** | CDN-compatible download resolution presets (640, 1024) |

## Features

- Inline image preview on all generation nodes
- Right-click context menu to auto-create and connect Preview/Save Image nodes
- Colored console logging with parameter summary
- In-memory image processing (no temp file I/O for downloads)
- Event-based progress reporting
- `ExecutionBlocker` for missing images (e.g., Upscale returns 1 image, remaining slots are blocked)

## Right-Click Menu

On Imagine, Vary, Pan, Upscale, and Download nodes:

- **Connect Preview Image(s)** - Creates and connects PreviewImage nodes in a 2x2 grid
- **Connect Save Image(s)** - Same layout with SaveImage nodes

## License

MIT
