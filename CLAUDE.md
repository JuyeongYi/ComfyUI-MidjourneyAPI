# ComfyUI-MidJourney

ComfyUI custom nodes for Midjourney image generation.

## Dependencies

- Midjourney Python API Client: `/mnt/c/Users/Jooyo/source/MJ_API`
  - Package name: `midjourney-api`
  - Main class: `MidjourneyClient` (`midjourney_api/client.py`)
  - Features: imagine, vary, upscale, pan, download
  - Auth: Firebase refresh token (`.env` in ComfyUI root)
  - HTTP: `curl_cffi` (Chrome TLS impersonation)

## Project Structure

| File | Role |
|------|------|
| `__init__.py` | Entry point — `comfy_entrypoint()` → `MidJourneyExtension` |
| `nodes.py` | Imagine / Vary / Upscale / Pan / Download nodes |
| `node_imagine_v7_params.py` | V7 parameter node (`ImagineV7Params`) |
| `node_params_io.py` | Save/Load Imagine Params nodes |
| `node_style.py` | Style Select node + `/mj/style_image` API route |
| `node_keywords.py` | Dynamically generates keyword nodes from `mj/keywords/` |
| `node_keyword_join.py` | Keyword Join node (Autogrow, up to 100 inputs) |
| `utils.py` | Shared utilities |
| `web/style_preview.js` | Instant in-node preview JS extension for Style Select |
| `web/autoconnect.js` | Right-click → auto-connect Preview/Save nodes |

## ComfyUI V3 API Patterns

- Nodes: inherit `io.ComfyNode`, implement `define_schema()` + `execute()` as classmethods
- Registration: `comfy_entrypoint()` in `__init__.py` returns a `MidJourneyExtension` whose `get_node_list()` returns all node classes
- JS extensions: `WEB_DIRECTORY = "./web"` — all `.js` files in `web/` are auto-loaded
- Backend API routes: `@PromptServer.instance.routes.get("/path")` registered at module import time (safe because custom nodes load after server starts)
- Instant node preview (no workflow run needed): set `node.imgs = [HTMLImageElement]` in JS + `app.graph?.setDirtyCanvas(true)`. See `PreviewLocalFile.md` for the full pattern.

## Style System

File format: `<name>__<sref_code>.<ext>` (e.g. `Glitch Noir__2206414533.webp`)

| Path | Purpose |
|------|---------|
| `mj/style/` | Plugin default styles |
| `<comfy_root>/user/mj/style/` | User custom styles (same name → user takes priority) |

## Keyword System

File location: `mj/keywords/<subcategory>/<category>.txt`
- Folder name → ComfyUI subcategory (`Midjourney/keywords/<Subcategory>`)
- File name → node display name (`shot_type.txt` → **Shot Type** node)
- `node_keywords.py` recursively scans on startup and generates nodes dynamically
- User additions: `<comfy_root>/user/mj/keywords/<subcategory>/` — same filename merges keywords (does not replace)
