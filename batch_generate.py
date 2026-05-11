"""Batch submit images to TRELLIS.2 and wait for completion."""
import base64
import json
import time
import sys
import os
import requests

GO_API = "http://localhost:9010/sceneApi/asset/jobs"
IMAGES = [
    ("/data/fj/数字孪生/asserts/草莓盆栽.png", "strawberry_potted"),
    ("/data/fj/数字孪生/asserts/大棚.jpg", "greenhouse"),
    ("/data/fj/数字孪生/asserts/大型灌溉机.png", "irrigation_machine"),
]

def submit_job(image_path, model_name):
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    payload = {
        "imageBase64": img_b64,
        "imageFileName": os.path.basename(image_path),
        "ownerKey": "admin",
        "resolution": 512,
        "decimationTarget": 300000,
        "textureSize": 2048,
    }
    resp = requests.post(GO_API, json=payload)
    data = resp.json()
    if data["code"] != 200:
        print(f"  ERROR submitting: {data}")
        return None
    job_id = data["data"]["jobId"]
    print(f"  Submitted: {job_id}")
    return job_id

def poll_job(job_id, timeout=600):
    url = f"{GO_API}/{job_id}"
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(url)
        data = resp.json()["data"]
        status = data["status"]
        progress = data.get("progress", 0)
        print(f"  [{status}] progress={progress}%", end="\r")
        if status == "completed":
            print(f"\n  ✅ Completed! GLB: {data.get('modelUrl')}, size: {data.get('fileSize', 0)/1e6:.1f}MB")
            return data
        elif status == "failed":
            print(f"\n  ❌ Failed: {data.get('errorMsg', 'unknown')}")
            return None
        time.sleep(5)
    print(f"\n  ⏰ Timeout")
    return None

def main():
    print("=" * 60)
    print("TRELLIS.2 Batch Generation")
    print("=" * 60)

    results = []
    for image_path, model_name in IMAGES:
        if not os.path.exists(image_path):
            print(f"\nSKIP: {image_path} not found")
            continue

        print(f"\n📷 {model_name} ({image_path})")
        job_id = submit_job(image_path, model_name)
        if not job_id:
            continue

        result = poll_job(job_id)
        if result:
            results.append(result)

    print("\n" + "=" * 60)
    print(f"Done! {len(results)}/{len(IMAGES)} generated successfully.")
    for r in results:
        print(f"  {r.get('modelUrl')}")


if __name__ == "__main__":
    main()
