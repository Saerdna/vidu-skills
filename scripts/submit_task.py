#!/usr/bin/env python3
"""
Submit a vidu task (text2video, img2video, headtailimg2video, character2video). Outputs task_id to stdout.

Usage:
  export VIDU_TOKEN=your_token
  python submit_task.py --type text2video --prompt "hello apple"
  python submit_task.py --type img2video --prompt "..." --image-uri "ssupload:?id=123"   # exactly 1 image
  python submit_task.py --type headtailimg2video --prompt "..." --image-uri id1 --image-uri id2   # exactly 2 (首帧,尾帧)
  python submit_task.py --type character2video --prompt "..." --image-uri id1 --image-uri id2 [...]  # 2-7 images, Q2 only, no transition
  python submit_task.py --body-file task_body.json

Options:
  --type text2video | img2video | headtailimg2video | character2video
  --prompt "text"           (required; one text prompt)
  --image-uri "ssupload:?id=X"  (img2video: 1; headtailimg2video: 2; character2video: 2-7)
  --duration 8  --resolution 1080p  --aspect-ratio "16:9"  (aspect_ratio omitted for img2video)
  --model-version 3.2 | 3.1  --transition pro | speed  (transition omitted for character2video and for text2video Q2)
  --body-file path         (use full JSON body from file instead of flags)

Output: task_id (one line). Exit: 0 on success.
"""

import argparse
import json
import os
import sys

try:
    import requests
except ImportError:
    print("install requests: pip install requests", file=sys.stderr)
    sys.exit(1)

BASE_URL = os.environ.get("VIDU_BASE_URL", "https://service.vidu.cn").rstrip("/")
TOKEN = os.environ.get("VIDU_TOKEN", "")
HEADERS = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": f"viduclawbot/1.0 (+{BASE_URL})",
}


def build_body(args: argparse.Namespace) -> dict:
    if args.body_file:
        with open(args.body_file, "r", encoding="utf-8") as f:
            return json.load(f)

    prompts = []
    for p in args.prompt or []:
        prompts.append({"type": "text", "content": p})
    for uri in args.image_uri or []:
        prompts.append({"type": "image", "content": uri})

    if not prompts:
        raise ValueError("At least one --prompt or --image-uri required")

    # Validate image count per type (see 任务支持列表)
    n_images = len(args.image_uri or [])
    if args.type == "img2video" and n_images != 1:
        raise ValueError("img2video requires exactly 1 --image-uri")
    if args.type == "headtailimg2video" and n_images != 2:
        raise ValueError("headtailimg2video requires exactly 2 --image-uri (首帧, 尾帧)")
    if args.type == "character2video":
        if n_images < 2 or n_images > 7:
            raise ValueError("character2video requires 2-7 --image-uri")

    settings = {
        "duration": args.duration,
        "resolution": args.resolution,
        "movement_amplitude": "auto",
        "sample_count": 1,
        "schedule_mode": "normal",
        "codec": args.codec,
        "model_version": "3.1" if args.type == "character2video" else args.model_version,
        "use_trial": False,
    }
    # img2video: do not pass aspect_ratio (determined by input image)
    if args.type != "img2video":
        settings["aspect_ratio"] = args.aspect_ratio
    # character2video and text2video Q2: do not pass transition
    if args.type != "character2video" and not (args.type == "text2video" and args.model_version == "3.1"):
        settings["transition"] = args.transition

    return {
        "input": {
            "prompts": prompts,
            "editor_mode": "normal",
            "enhance": True,
        },
        "type": args.type,
        "settings": settings,
    }


def main() -> int:
    if not TOKEN:
        print("VIDU_TOKEN is not set", file=sys.stderr)
        return 1

    ap = argparse.ArgumentParser(description="Submit vidu task")
    ap.add_argument("--type", choices=("text2video", "img2video", "headtailimg2video", "character2video"), default="text2video")
    ap.add_argument("--prompt", action="append", help="Text prompt (repeat for multiple)")
    ap.add_argument("--image-uri", action="append", help="ssupload:?id=... for img2video")
    ap.add_argument("--duration", type=int, default=8)
    ap.add_argument("--resolution", default="1080p")
    ap.add_argument("--aspect-ratio", default="16:9")
    ap.add_argument("--model-version", default="3.2")
    ap.add_argument("--transition", default="pro")
    ap.add_argument("--codec", default="h265")
    ap.add_argument("--body-file", help="Path to full JSON body file")
    args = ap.parse_args()

    try:
        body = build_body(args)
    except Exception as e:
        print(e, file=sys.stderr)
        return 1

    url = f"{BASE_URL}/vidu/v1/tasks"
    r = requests.post(url, json=body, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    task_id = data.get("id")
    if task_id is None:
        print("Response missing id", file=sys.stderr)
        return 1
    print(task_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
