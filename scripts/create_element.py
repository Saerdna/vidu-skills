#!/usr/bin/env python3
"""
Create a material element (subject) for use in character2video: upload 1-3 images,
provide name and description, POST to /vidu/v1/material/elements.

Usage:
  export VIDU_TOKEN=your_token
  python create_element.py --name "机器猫" --description "哆啦A梦，一个蓝白相间的卡通机器人..." --image ./a.jpg
  python create_element.py --name "艾莉娅" --description "..." --style "2D动画" --image ./main.jpg --image ./aux1.jpg

Options:
  --name "text"             (required) subject name
  --description "text"      (required) subject description
  --style "text"            (optional) e.g. "2D动画，卡通"
  --image path              (required) 1-3 image paths; first is main, rest auxiliary

Output: One JSON line with element id and version, e.g. {"id": "123", "version": "456"}.
Exit: 0 on success, non-zero on failure.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def run_upload(path: str) -> str:
    """Run upload_image.py for one image; return ssupload:?id=... or raise."""
    r = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "upload_image.py"), path],
        capture_output=True,
        text=True,
        cwd=SCRIPT_DIR,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr or r.stdout or "upload failed")
    return (r.stdout or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Create material element (创建主体)")
    ap.add_argument("--name", required=True, help="Subject name")
    ap.add_argument("--description", required=True, help="Subject description")
    ap.add_argument("--style", default="", help="Optional style e.g. 2D动画，卡通")
    ap.add_argument("--image", action="append", dest="images", required=True, help="Image path (1-3); first=main, rest=auxiliary")
    args = ap.parse_args()

    images = args.images or []
    if len(images) < 1 or len(images) > 3:
        print(json.dumps({"error": "create_element requires 1-3 --image paths"}), file=sys.stderr)
        return 1

    for p in images:
        if not Path(p).is_file():
            print(json.dumps({"error": f"Image not found: {p}"}), file=sys.stderr)
            return 1

    # Upload each image; same ssupload id used for content and src_img per component
    ssuploads = []
    try:
        for path in images:
            ssuploads.append(run_upload(path))
    except RuntimeError as e:
        print(json.dumps({"error": "upload failed", "detail": str(e)}), file=sys.stderr)
        return 1

    components = []
    for i, uri in enumerate(ssuploads):
        comp_type = "main" if i == 0 else "auxiliary"
        components.append({
            "type": comp_type,
            "content": uri,
            "src_img": uri,
            "content_type": "image",
        })

    recaption = {"description": args.description}
    if args.style:
        recaption["style"] = args.style
    body = {
        "name": args.name,
        "modality": "image",
        "type": "user",
        "components": components,
        "version": "0",
        "recaption": recaption,
    }

    import os
    import requests
    base = os.environ.get("VIDU_BASE_URL", "https://service.vidu.cn").rstrip("/")
    token = os.environ.get("VIDU_TOKEN", "")
    if not token:
        print(json.dumps({"error": "VIDU_TOKEN is not set"}), file=sys.stderr)
        return 1
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
        "User-Agent": f"viduclawbot/1.0 (+{base})",
    }
    url = f"{base}/vidu/v1/material/elements"
    try:
        r = requests.post(url, json=body, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        out = {"id": str(data.get("id", "")), "version": str(data.get("version", ""))}
        print(json.dumps(out))
        return 0
    except requests.RequestException as e:
        err = {"error": "create element failed"}
        if hasattr(e, "response") and e.response is not None:
            try:
                err["body"] = e.response.json()
            except Exception:
                err["text"] = e.response.text[:500]
        else:
            err["detail"] = str(e)
        print(json.dumps(err), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
