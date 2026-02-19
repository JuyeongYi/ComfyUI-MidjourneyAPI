# ComfyUI-MidJourney

Custom nodes for ComfyUI that generate Midjourney images via [midjourney-api](https://github.com/JuyeongYi/PythonMidjourneyAPIClient).

> Korean documentation: [README.md](README.md)

---

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

3. Place a `.env` file in the **ComfyUI root** directory for authentication.
   See [PythonMidjourneyAPIClient](https://github.com/JuyeongYi/PythonMidjourneyAPIClient) for authentication details.

---

## Nodes

### Image Generation

| Node | Description | Outputs |
|------|-------------|---------|
| **MidJourney Imagine** | Text-to-image generation | 4 images + job_id |
| **MidJourney Vary** | Strong/Subtle variation | 4 images + job_id |
| **MidJourney Upscale** | 2× upscale (subtle/creative) | 1 image + job_id |
| **MidJourney Pan** | Directional image extension | 4 images + job_id |
| **MidJourney Download** | Download images by job ID | 4 images |

### Parameters

| Node | Description |
|------|-------------|
| **Imagine V7 Params** | V7 parameter configuration (aspect ratio, stylize, chaos, seed, quality, raw, tile, sref, oref, personalize, visibility, etc.) |
| **Save Imagine Params** | Save parameters as a JSON preset |
| **Load Imagine Params** | Load parameters from a JSON preset |

### Style

| Node | Description |
|------|-------------|
| **Style Select** | Select a `--sref` code from style image files with instant in-node preview |

### Keywords

**Keyword Join** — Combines multiple keyword strings into one (separator: `, ` / ` ` / ` | ` / ` + `, up to 100 inputs).

**Per-category keyword nodes** — Each outputs the selected keyword as a String. Found under `Midjourney/keywords/<category>` in the node menu.

| Category | Nodes | Included |
|----------|-------|----------|
| **Photography** | 9 | Shot Type, Lens, Camera Effect, Film Stock, Camera Body, Composition, Perspective, Post Processing, Detail Quality |
| **Lighting** | 3 | Lighting, Color Tone, Mood |
| **Environment** | 7 | Environment, Natural Landscape, Underwater Scene, Urban Setting, Weather, Season, Celestial |
| **Art Style** | 6 | Art Style, Art Medium, Era Aesthetic, Illustration Style, Print Technique, Street Art Style |
| **Digital Fx** | 6 | Render Engine, Game Art Style, Vfx Style, Glitch Aesthetic, Dimensionality, Particle Effects |
| **Character** | 5 | Facial Expression, Hair Style, Makeup Style, Subject Pose, Fashion Clothing |
| **Architecture** | 3 | Architectural Style, Interior Design, Building Type |
| **Culture** | 6 | Cultural Aesthetic, Cultural Ritual, Mythological Theme, Genre Narrative, Music Genre Aesthetic, Artist Reference |
| **Material** | 4 | Texture Material, Material Finish, Pattern Design, Typography Style |
| **Subject** | 7 | Flora Style, Creature Type, Sport Activity, Food Styling, Vehicle Type, Scientific Visualization, Data Visualization |

Total: **56 category files, ~1,845 keywords**.

---

## Features

- Inline image preview on all generation nodes
- Right-click context menu to auto-create and connect Preview/Save Image nodes
- Colored console logging with parameter summary
- In-memory image processing for downloads (no temp file I/O)
- Event-based progress reporting
- `ExecutionBlocker` for missing image slots (e.g., Upscale returns 1 image, remaining 3 slots are blocked)

---

## Right-Click Menu

On Imagine, Vary, Pan, Upscale, and Download nodes:

- **Connect Preview Image(s)** — Creates and connects PreviewImage nodes in a 2×2 grid
- **Connect Save Image(s)** — Same layout with SaveImage nodes

---

## Customization

### Adding Style Files

Place image files in `mj/style/` or `<ComfyUI root>/user/mj/style/`:

```
<style name>__<sref code>.<extension>

Examples:
  Glitch Noir__2206414533.webp
  Golden Hour__1938472650.png
```

- Supported extensions: `.jpg` `.jpeg` `.png` `.webp` `.gif`
- If the same name exists in both locations, the `user/` path takes priority
- The Style Select node shows an **instant in-node preview** as soon as it is placed on the canvas

### Adding Keyword Files

Add `.txt` files under `<ComfyUI root>/user/mj/keywords/<subcategory>/`:

```
user/mj/keywords/
  photography/
    my_custom.txt    ← registered as a new keyword node
  lighting/
    lighting.txt     ← keywords merged into the existing lighting node
```

- The filename becomes the node display name (`my_custom.txt` → **My Custom** node)
- The folder name becomes the ComfyUI menu subcategory
- Same filename: user keywords are appended after plugin keywords (not replaced)
- One keyword per line; lines starting with `#` are treated as comments

---

## License

MIT
