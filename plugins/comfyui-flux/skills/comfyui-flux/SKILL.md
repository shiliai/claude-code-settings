---
name: comfyui-flux
description: Generate images using ComfyUI with Flux models via API. Use when the user asks to create, generate images with Flux, ComfyUI, or mentions local image generation tasks. Supports Flux 1 and Flux 2 models with various photography and art styles.
allowed-tools: Read, Write, Glob, Grep, Task, Bash(cat:*), Bash(ls:*), Bash(tree:*), Bash(python3:*)
---

# ComfyUI Flux Image Generation Skill

Generate AI images using ComfyUI's Flux models through the HTTP API. This skill provides both a Python API and command-line interface for local image generation.

## Requirements

1. **ComfyUI Server**: Must be running on `http://localhost:8188` (default)
2. **Flux Models**: Available in `/models/unet/` directory:
   - `flux1-dev-fp8.safetensors` - 11GB, faster generation
   - `flux2-dev.safetensors` - 64GB, higher quality
3. **Dependencies**: Python 3 with `urllib` (standard library)
4. **Hardware**: Minimum 16GB VRAM for Flux 1, 64GB+ for Flux 2

## Quick Start

### Generate an image with default settings

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/comfyui-flux/generate.py \
  "a cute cat riding a scooter, wearing sunglasses"
```

### Generate with specific model and size

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/comfyui-flux/generate.py \
  "cyberpunk cityscape at night, neon lights" \
  --model flux2-dev.safetensors \
  --width 1280 --height 720 \
  --steps 30 \
  -o /tmp/cyberpunk.png
```

## Available Options

### Models (--model)

- `flux1-dev-fp8.safetensors` (default) - 11GB, ~60-90s generation
- `flux2-dev.safetensors` - 64GB, higher quality, slower generation

### Dimensions

- `1024x1024` (default) - Square, good for most purposes
- `832x1216` - Portrait (2:3)
- `1216x832` - Landscape (3:2)
- `1280x720` - HD widescreen
- Custom sizes supported (multiples of 16)

### Steps (--steps)

- `20` (default) - Good balance of speed and quality
- `30-50` - Higher quality, slower generation
- `10-15` - Faster, draft quality

### Guidance Scale (--guidance)

- `3.5` (default) - Balanced
- `2.0-3.0` - More creative/freedom
- `4.0-5.0` - More prompt adherence

## Photography Style Templates

See `${CLAUDE_PLUGIN_ROOT}/skills/comfyui-flux/references/prompt-templates.md` for comprehensive prompt templates.

### Modern Photorealism
```
Professional studio portrait of [subject], shot on Sony A7IV, 
clean sharp focus, high dynamic range, 85mm lens, f/1.4, 
soft natural lighting, neutral background
```

### Analog Film
```
[Subject], shot on Kodak Portra 400, natural film grain, 
organic warm colors, soft vignette, vintage aesthetic
```

### 2000s Digicam
```
[Subject], early 2000s digicam style, slight digital noise, 
flash photography, candid moment, Y2K aesthetic
```

### Product Photography
```
[Product] product photography, floating on gradient background, 
soft studio lighting, minimal shadows, clean composition, 
professional commercial photography
```

## Python API Usage

```python
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/skills/comfyui-flux')
from generate import generate_image

result = generate_image(
    prompt_text="a beautiful mountain landscape at sunset",
    model_name="flux1-dev-fp8.safetensors",
    width=1024,
    height=1024,
    steps=20,
    seed=None,  # Random seed
    guidance=3.5
)

if result['success']:
    with open('/tmp/output.png', 'wb') as f:
        f.write(result['images'][0]['data'])
    print(f"Generated in {result['elapsed_time']:.1f}s")
```

## Workflow

1. **Check ComfyUI Status**: Verify server is running at localhost:8188
2. **Select Model**: Choose between Flux 1 (fast) or Flux 2 (quality)
3. **Build Prompt**: Use templates from references/prompt-templates.md
4. **Generate**: Run generation with desired parameters
5. **Review**: Image is saved to specified output path

## Error Handling

If generation fails:

- Check ComfyUI is running: `curl http://localhost:8188/system_stats`
- Verify model files exist in container: `docker exec comfyui ls /models/unet/`
- Check VRAM availability: Models require 16GB+ for Flux 1, 64GB+ for Flux 2
- Ensure output directory is writable

## Best Practices

1. **Prompt Structure**: Subject → Action → Style → Context (in that order)
2. **Word Count**: 30-80 words ideal for Flux models
3. **Specific Camera References**: Mention "Sony A7IV", "Kodak Portra 400" for authentic looks
4. **Lighting**: Always specify lighting style (golden hour, soft box, natural window)
5. **Start Small**: Test with Flux 1 at 1024x1024, 20 steps before scaling up
6. **Seed for Consistency**: Use same seed to reproduce similar results

## References

- [Prompt Templates](references/prompt-templates.md) - Comprehensive style templates
- [Flux Model Comparison](https://blackforestlabs.ai/) - Official Flux documentation
- [ComfyUI Documentation](https://docs.comfyui.org/) - ComfyUI API reference
