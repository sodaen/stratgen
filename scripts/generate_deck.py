#!/usr/bin/env python3
"""
CLI Generator für große Präsentationen.
Umgeht Gunicorn-Timeout-Probleme.

Verwendung:
    python scripts/generate_deck.py --topic "Mein Thema" --slides 150 --output data/exports/mein-deck.pptx
"""

import sys
import os
import time
import json
import asyncio
import argparse
from pathlib import Path

sys.path.insert(0, '/home/sodaen/stratgen')

from services.live_generator import start_generation, live_generator


def main():
    parser = argparse.ArgumentParser(description='Generate PowerPoint presentation')
    parser.add_argument('--topic', required=True, help='Presentation topic')
    parser.add_argument('--brief', default='', help='Detailed brief')
    parser.add_argument('--customer', default='', help='Customer name')
    parser.add_argument('--industry', default='', help='Industry')
    parser.add_argument('--slides', type=int, default=50, help='Number of slides')
    parser.add_argument('--output', default='', help='Output PPTX path')
    parser.add_argument('--json', action='store_true', help='Output JSON instead of PPTX')
    
    args = parser.parse_args()
    
    print(f"╔═══════════════════════════════════════════════════════════════════╗")
    print(f"║  STRATGEN CLI GENERATOR                                           ║")
    print(f"╚═══════════════════════════════════════════════════════════════════╝")
    print()
    print(f"Topic: {args.topic}")
    print(f"Slides: {args.slides}")
    print()
    
    # Start generation
    request = {
        "topic": args.topic,
        "brief": args.brief or f"Erstelle eine professionelle Präsentation zu: {args.topic}",
        "customer_name": args.customer,
        "industry": args.industry,
        "deck_size": args.slides,
        "enable_charts": True,
        "enable_images": False
    }
    
    result = start_generation(request)
    generation_id = result.get("generation_id")
    
    if not generation_id:
        print(f"ERROR: {result}")
        sys.exit(1)
    
    print(f"Generation ID: {generation_id}")
    print()
    
    # Run generation
    start_time = time.time()
    
    async def generate():
        slides = []
        
        async for event in live_generator.generate_async(generation_id):
            event_type = event.get("type")
            
            if event_type == "slide_ready":
                slide = event.get("data", {}).get("slide", {})
                slides.append(slide)
                elapsed = time.time() - start_time
                title = slide.get('title', 'Untitled')[:50]
                knowledge = '📚' if slide.get('knowledge_used') else ''
                print(f"  [{elapsed:5.1f}s] Slide {len(slides):3d}/{args.slides}: {title} {knowledge}")
            
            elif event_type == "complete":
                break
            
            elif event_type == "error":
                print(f"ERROR: {event.get('data', {}).get('message')}")
                break
        
        return slides
    
    slides = asyncio.run(generate())
    
    duration = time.time() - start_time
    knowledge_count = sum(1 for s in slides if s.get('knowledge_used'))
    
    print()
    print(f"═══════════════════════════════════════════════════════════════════")
    print(f"  Generiert: {len(slides)} Slides in {duration:.1f}s ({len(slides)/duration*60:.1f} slides/min)")
    print(f"  Knowledge: {knowledge_count}/{len(slides)} Slides")
    print()
    
    # Export
    if args.json:
        output_path = args.output or f"data/exports/{generation_id}.json"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump({
                "generation_id": generation_id,
                "topic": args.topic,
                "slides": slides,
                "duration_seconds": duration
            }, f, indent=2, ensure_ascii=False)
        
        print(f"  JSON: {output_path}")
    else:
        # PPTX Export
        try:
            from services.pptx_designer_v2 import PPTXDesignerV2
            
            colors = {
                "primary": "#1E40AF",
                "secondary": "#3B82F6",
                "accent": "#10B981",
                "background": "#FFFFFF",
                "text": "#111827"
            }
            
            designer = PPTXDesignerV2(colors=colors)
            pptx_bytes = designer.create_presentation(
                slides=slides,
                title=args.topic,
                company=args.customer,
                include_sources_slide=True
            )
            
            output_path = args.output or f"data/exports/{generation_id}.pptx"
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(pptx_bytes)
            
            size_kb = os.path.getsize(output_path) / 1024
            print(f"  PPTX: {output_path} ({size_kb:.1f} KB)")
            
        except Exception as e:
            print(f"  PPTX Export Error: {e}")
            # Fallback to JSON
            output_path = f"data/exports/{generation_id}.json"
            with open(output_path, 'w') as f:
                json.dump({"slides": slides}, f)
            print(f"  Fallback JSON: {output_path}")
    
    print()


if __name__ == "__main__":
    main()
