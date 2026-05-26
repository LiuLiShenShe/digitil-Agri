from pathlib import Path
from statistics import mean

from PIL import Image
from playwright.sync_api import expect, sync_playwright


PROMPT = "搭建番茄温室，包含 20 株番茄、气象站、水泵、摄像头和传感器"
FRONTEND_URL = "http://127.0.0.1:5174/scene/"
SCREENSHOT_PATH = Path("/tmp/tomato-greenhouse-visual-acceptance.png")


def average_luma(path: Path) -> float:
    image = Image.open(path).convert("RGB")
    width, height = image.size
    crop = image.crop((int(width * 0.25), int(height * 0.12), int(width * 0.96), int(height * 0.94)))
    pixels = list(crop.resize((160, 120)).getdata())
    return mean(0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in pixels)


def assert_snapshot(snapshot: dict):
    assert snapshot, "visual acceptance snapshot is missing"
    assert snapshot["templateKey"] == "tomato_greenhouse_visual_template"
    greenhouse = snapshot["greenhouse"]
    tomatoes = snapshot["tomatoes"]
    irrigation = snapshot["irrigation"]
    lighting = snapshot["lighting"]

    assert len(tomatoes) == 20, f"tomato count = {len(tomatoes)}, want 20"
    half_w = greenhouse["width"] / 2
    half_d = greenhouse["depth"] / 2
    center = greenhouse["center"]
    for tomato in tomatoes:
        dx = abs(tomato["x"] - center["x"])
        dz = abs(tomato["z"] - center["z"])
        assert dx <= half_w - 30, f"tomato x outside greenhouse: {tomato}"
        assert dz <= half_d - 30, f"tomato z outside greenhouse: {tomato}"
        assert 0 < tomato["scale"] <= 3, f"tomato scale out of range: {tomato}"

    assert irrigation["bedCount"] >= 4
    assert irrigation["dripLineCount"] >= 8
    assert irrigation["mainPipeLength"] >= greenhouse["width"] * 0.7
    assert irrigation["valveCount"] >= 4
    assert lighting["minimumScreenshotLuma"] >= 80


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 960}, device_scale_factor=1)
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.goto(FRONTEND_URL, wait_until="networkidle")

        page.get_by_text("AI搭建").click()
        textarea = page.locator(".semantic-builder textarea").first
        textarea.fill(PROMPT)
        page.get_by_role("button", name="生成并搭建").click()

        page.wait_for_function(
            "() => window.__tomatoGreenhouseVisualAcceptance && window.__tomatoGreenhouseVisualAcceptance.tomatoes.length === 20",
            timeout=45000,
        )
        page.wait_for_timeout(2500)
        snapshot = page.evaluate("window.__tomatoGreenhouseVisualAcceptance")
        assert_snapshot(snapshot)

        page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
        luma = average_luma(SCREENSHOT_PATH)
        assert luma >= snapshot["lighting"]["minimumScreenshotLuma"], f"average luma {luma:.2f} below threshold"
        ignored_console_fragments = (
            "Failed to load resource",
            "没有找到 context-menu 对应的实例",
        )
        unexpected_errors = [
            err for err in console_errors
            if not any(fragment in err for fragment in ignored_console_fragments)
        ]
        assert not unexpected_errors, unexpected_errors
        print(f"PASS screenshot={SCREENSHOT_PATH} average_luma={luma:.2f}")
        browser.close()


if __name__ == "__main__":
    main()
