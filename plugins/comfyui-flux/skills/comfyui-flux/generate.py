#!/usr/bin/env python3
"""
ComfyUI Flux API Client
Generate images using ComfyUI with Flux models via HTTP API
"""

import json
import urllib.request
import urllib.parse
import random
import time
import sys
import argparse

COMFYUI_URL = "http://localhost:8188"


def queue_prompt(prompt_workflow, client_id="comfyui_flux_skill"):
    """Submit workflow to ComfyUI"""
    p = {"prompt": prompt_workflow, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise RuntimeError(f"API Error: {error_body}")


def get_history(prompt_id):
    """Get generation history"""
    with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())


def get_image(filename, subfolder, folder_type):
    """Download generated image"""
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{COMFYUI_URL}/view?{url_values}") as response:
        return response.read()


def build_flux_workflow(prompt_text, model_name, width, height, seed, steps, output_prefix, guidance):
    """Build Flux workflow JSON"""
    return {
        "1": {
            "inputs": {"unet_name": model_name, "weight_dtype": "default"},
            "class_type": "UNETLoader",
            "_meta": {"title": "Load Diffusion Model"}
        },
        "2": {
            "inputs": {
                "clip_name1": "t5xxl_fp16.safetensors",
                "clip_name2": "clip_l.safetensors",
                "type": "flux"
            },
            "class_type": "DualCLIPLoader",
            "_meta": {"title": "DualCLIPLoader"}
        },
        "3": {
            "inputs": {"vae_name": "flux-vae-bf16.safetensors"},
            "class_type": "VAELoader",
            "_meta": {"title": "Load VAE"}
        },
        "4": {
            "inputs": {
                "clip": ["2", 0],
                "clip_l": prompt_text,
                "t5xxl": prompt_text,
                "guidance": guidance
            },
            "class_type": "CLIPTextEncodeFlux",
            "_meta": {"title": "CLIPTextEncodeFlux"}
        },
        "5": {
            "inputs": {"width": width, "height": height, "batch_size": 1},
            "class_type": "EmptyFlux2LatentImage",
            "_meta": {"title": "Empty Flux 2 Latent"}
        },
        "6": {
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler",
            "_meta": {"title": "KSampler"}
        },
        "7": {
            "inputs": {"samples": ["6", 0], "vae": ["3", 0]},
            "class_type": "VAEDecode",
            "_meta": {"title": "VAE Decode"}
        },
        "8": {
            "inputs": {"filename_prefix": output_prefix, "images": ["7", 0]},
            "class_type": "SaveImage",
            "_meta": {"title": "Save Image"}
        }
    }


def generate_image(prompt_text, model_name="flux1-dev-fp8.safetensors",
                   width=1024, height=1024, seed=None, steps=20,
                   output_prefix="flux_gen", guidance=3.5):
    """
    Generate image using Flux model via ComfyUI API
    
    Args:
        prompt_text: Text prompt for image generation
        model_name: Model filename (flux1-dev-fp8.safetensors or flux2-dev.safetensors)
        width: Image width (multiples of 16)
        height: Image height (multiples of 16)
        seed: Random seed (None for random)
        steps: Sampling steps (10-50)
        output_prefix: Output filename prefix
        guidance: Guidance scale (1.0-10.0)
    
    Returns:
        dict: {success, prompt_id, seed, elapsed_time, images, error}
    """
    if seed is None:
        seed = random.randint(1, 9999999999)
    
    workflow = build_flux_workflow(
        prompt_text, model_name, width, height,
        seed, steps, output_prefix, guidance
    )
    
    response = queue_prompt(workflow)
    prompt_id = response['prompt_id']
    
    start_time = time.time()
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            outputs = history[prompt_id].get('outputs', {})
            if outputs:
                for node_id, node_output in outputs.items():
                    if 'images' in node_output:
                        images = []
                        for img_info in node_output['images']:
                            image_data = get_image(
                                img_info['filename'],
                                img_info.get('subfolder', ''),
                                img_info.get('type', 'output')
                            )
                            images.append({
                                'filename': img_info['filename'],
                                'data': image_data
                            })
                        
                        return {
                            'success': True,
                            'prompt_id': prompt_id,
                            'seed': seed,
                            'elapsed_time': time.time() - start_time,
                            'images': images
                        }
            break
        time.sleep(2)
    
    return {'success': False, 'error': 'Generation failed or timeout'}


def main():
    parser = argparse.ArgumentParser(
        description='Generate images using ComfyUI Flux API'
    )
    parser.add_argument('prompt', help='Text prompt for image generation')
    parser.add_argument('--model', default='flux1-dev-fp8.safetensors',
                       help='Model filename (default: flux1-dev-fp8.safetensors)')
    parser.add_argument('--width', type=int, default=1024, help='Image width')
    parser.add_argument('--height', type=int, default=1024, help='Image height')
    parser.add_argument('--steps', type=int, default=20, help='Sampling steps')
    parser.add_argument('--seed', type=int, default=None, help='Random seed')
    parser.add_argument('--output', '-o', default='/tmp/flux_output.png',
                       help='Output file path')
    parser.add_argument('--guidance', type=float, default=3.5,
                       help='Guidance scale (default: 3.5)')
    parser.add_argument('--prefix', default='flux_gen',
                       help='Output filename prefix')
    
    args = parser.parse_args()
    
    print(f"🎨 Generating with Flux...")
    print(f"📝 Prompt: {args.prompt}")
    print(f"🤖 Model: {args.model}")
    print(f"📐 Size: {args.width}x{args.height}")
    
    result = generate_image(
        prompt_text=args.prompt,
        model_name=args.model,
        width=args.width,
        height=args.height,
        seed=args.seed,
        steps=args.steps,
        output_prefix=args.prefix,
        guidance=args.guidance
    )
    
    if result['success']:
        if result['images']:
            with open(args.output, 'wb') as f:
                f.write(result['images'][0]['data'])
        print(f"✅ Image saved: {args.output}")
        print(f"⏱️  Time: {result['elapsed_time']:.1f}s")
        print(f"🎲 Seed: {result['seed']}")
        return 0
    else:
        print(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
