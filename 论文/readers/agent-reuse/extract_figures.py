#!/usr/bin/env python3
"""
Extract figures, tables, and algorithms from the Chinese academic PDF.

Strategy:
1. Cluster ALL vector drawings on each page (keep thin chart lines)
2. Match clusters to captions (filtered real captions only)
3. Also extract Algorithm 1 as text pseudocode
4. For embedded raster images, use pdfimages output (fig01-04.jpg)
"""
import fitz, os, re
from collections import defaultdict

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
lunwen_dir = os.path.dirname(os.path.dirname(script_dir))
pdf_path = os.path.join(lunwen_dir, "面向大语言模型驱动的智能体的计划复用机制.pdf")
assets_dir = os.path.join(script_dir, "assets")
os.makedirs(assets_dir, exist_ok=True)

doc = fitz.open(pdf_path)
PAGE_COUNT = doc.page_count

def get_col_mid(page):
    """Determine column split x-coordinate.
    Computed once on first page and cached; same across all pages in this PDF."""
    pw = page.rect.width
    # Only consider text blocks in the top 60% of the page (body text area)
    # to avoid full-width figure labels that span both columns
    ph = page.rect.height
    lx2, rx0 = 0, pw
    lcount, rcount = 0, 0
    for b in page.get_text("dict")["blocks"]:
        if b["type"] != 0: continue
        by1 = b["bbox"][3]
        if by1 > ph * 0.55: continue  # skip bottom half (full-width figures)
        bx0 = b["bbox"][0]
        if bx0 < pw * 0.35:
            lx2 = max(lx2, b["bbox"][2])
            lcount += 1
        elif bx0 > pw * 0.55:
            rx0 = min(rx0, bx0)
            rcount += 1
    if lcount >= 2 and rcount >= 2:
        return (lx2 + rx0) / 2
    return pw / 2

def get_drawing_clusters(page):
    """Cluster ALL drawings (including thin chart lines) by spatial proximity."""
    pw = page.rect.width
    col_mid = get_col_mid(page)
    drawings = page.get_drawings()
    if not drawings:
        return []

    # Filter: only remove full-width header rules
    filtered = []
    for d in drawings:
        r = d["rect"]
        h, w = r.y1 - r.y0, r.x1 - r.x0
        # Skip thin full-width horizontal rules (page headers/footers)
        if h < 3 and w > pw * 0.6:
            continue
        # Keep everything else (including thin chart lines)
        filtered.append(r)

    if not filtered:
        return []

    filtered.sort(key=lambda r: r.y0)
    clusters = []
    current = [filtered[0]]
    for r in filtered[1:]:
        prev_bot = max(c.y1 for c in current)
        if r.y0 - prev_bot <= 40:
            current.append(r)
        else:
            y0 = min(c.y0 for c in current); y1 = max(c.y1 for c in current)
            x0 = min(c.x0 for c in current); x1 = max(c.x1 for c in current)
            gh = y1 - y0
            if gh > 10 or len(current) >= 5:
                mx = (x0 + x1) / 2; gw = x1 - x0
                col = "full" if gw > pw * 0.5 else ("left" if mx < col_mid else "right")
                clusters.append({"y0": y0, "y1": y1, "x0": x0, "x1": x1,
                                "count": len(current), "col": col})
            current = [r]
    if current:
        y0 = min(c.y0 for c in current); y1 = max(c.y1 for c in current)
        x0 = min(c.x0 for c in current); x1 = max(c.x1 for c in current)
        gh = y1 - y0
        if gh > 10 or len(current) >= 5:
            mx = (x0 + x1) / 2; gw = x1 - x0
            col = "full" if gw > pw * 0.5 else ("left" if mx < col_mid else "right")
            clusters.append({"y0": y0, "y1": y1, "x0": x0, "x1": x1,
                            "count": len(current), "col": col})
    return clusters

def find_real_captions(page):
    """Find real captions (not body text references)."""
    pw = page.rect.width
    col_mid = get_col_mid(page)
    all_blocks = [b for b in page.get_text("dict")["blocks"] if b["type"] == 0]
    all_blocks.sort(key=lambda b: b["bbox"][1])

    def get_block_text(b):
        return " ".join("".join(s["text"] for s in line.get("spans", []))
                       for line in b.get("lines", []))

    def get_col(bbox):
        x0, x2 = bbox[0], bbox[2]
        if x0 < col_mid and x2 > col_mid + 10:
            return "full"
        return "left" if x2 < col_mid else "right"

    captions = []
    for b in all_blocks:
        bcol = get_col(b["bbox"])
        by0 = b["bbox"][1]

        for line in b.get("lines", []):
            lt = "".join(s["text"] for s in line.get("spans", []))
            m = re.match(r'(Fig\.|Figure|图|Table|表|算法|Algorithm)\s*(\d+)', lt.strip())
            if not m:
                continue

            kw, num = m.group(1), int(m.group(2))

            # Algorithms are always real captions
            if kw in ("算法", "Algorithm"):
                captions.append({"kw": kw, "num": num,
                                "bbox": b["bbox"], "text": lt.strip()[:120],
                                "col": bcol})
                break

            # Get blocks above in same column, sorted from nearest to farthest
            above = []
            for b2 in all_blocks:
                if b2 is b: continue
                if get_col(b2["bbox"]) != bcol: continue
                if b2["bbox"][3] < by0:
                    above.append(b2)
            above.sort(key=lambda x: x["bbox"][1], reverse=True)

            # Always check verb filter first -- body text refs start with verbs
            remaining = lt.strip()
            remaining = re.sub(r'^(Fig\.|Figure|图|Table|表|算法|Algorithm)\s*\d+\s*', '', remaining).strip()
            body_verbs = ['展示', '表明', '说明', '给出', '显示', '可以看到',
                         '可以看', '中可以看到', '列出', '总结了', '对比了',
                         '所示', '从中']
            if any(remaining.startswith(v) for v in body_verbs):
                continue  # Body text reference, skip

            if not above:
                captions.append({"kw": kw, "num": num,
                                "bbox": b["bbox"], "text": lt.strip()[:120],
                                "col": bcol})
                break

            # Heuristic: check first few blocks above for text length
            # Figure labels are short (<20 chars avg), body text is long
            sample = above[:min(3, len(above))]
            avg_len = sum(len(get_block_text(b2)) for b2 in sample) / len(sample)

            if avg_len < 25:
                # Short text above = figure labels = real caption
                captions.append({"kw": kw, "num": num,
                                "bbox": b["bbox"], "text": lt.strip()[:120],
                                "col": bcol})
                break

            # Walk back through blocks looking for a large gap (figure boundary)
            # or short text (figure label reaching back)
            is_body = True
            prev_y1 = by0
            for i, b2 in enumerate(above):
                gap = prev_y1 - b2["bbox"][3]
                blen = len(get_block_text(b2))
                if gap > 25 or blen < 15:
                    is_body = False
                    break
                prev_y1 = b2["bbox"][1]
                if i >= 10:
                    break

            if not is_body:
                captions.append({"kw": kw, "num": num,
                                 "bbox": b["bbox"], "text": lt.strip()[:120],
                                 "col": bcol})
            break

    return captions

def group_captions_by_proximity(captions, max_gap=30):
    """Group captions that are close together (same figure, multi-language).
    Captions for different figures on the same page should NOT be grouped."""
    caps = sorted(captions, key=lambda c: c["bbox"][1])
    groups = []
    used = [False] * len(caps)

    for i, c in enumerate(caps):
        if used[i]:
            continue
        group = [c]
        used[i] = True
        for j, c2 in enumerate(caps):
            if used[j]:
                continue
            if c2["num"] == c["num"] and cap_family(c2["kw"]) == cap_family(c["kw"]):
                # Close vertically?
                if abs(c2["bbox"][1] - c["bbox"][1]) <= max_gap:
                    group.append(c2)
                    used[j] = True
        groups.append(group)

    return groups

def cap_family(kw):
    if kw in ("Fig.", "Figure", "图"): return "figure"
    if kw in ("Table", "表"): return "table"
    if kw in ("算法", "Algorithm"): return "algorithm"
    return "other"

# ===== Phase 1: Find all real captions =====
print("="*60)
print("PHASE 1: Captions (filtered)")
print("="*60)

all_groups = []
for pg in range(PAGE_COUNT):
    page = doc[pg]
    caps = find_real_captions(page)
    if caps:
        groups = group_captions_by_proximity([{"page": pg, **c} for c in caps])
        for grp in groups:
            texts = [f"{c['kw']}{c['num']}: {c['text'][:60]}" for c in grp]
            print(f"  P{pg+1} {cap_family(grp[0]['kw'])}#{grp[0]['num']}: {' | '.join(texts)}")
        all_groups.extend(groups)

# ===== Phase 2: Drawing clusters =====
print("\n"+"="*60)
print("PHASE 2: Drawing Clusters")
print("="*60)
all_clusters = {}
for pg in range(PAGE_COUNT):
    clusters = get_drawing_clusters(doc[pg])
    if clusters:
        all_clusters[pg] = clusters
        for i, c in enumerate(clusters):
            print(f"  P{pg+1} c{i}: y=({c['y0']:.0f},{c['y1']:.0f}) "
                  f"x=({c['x0']:.0f},{c['x1']:.0f}) n={c['count']} col={c['col']}")

# ===== Phase 3: Match & Extract =====
print("\n"+"="*60)
print("PHASE 3: Extraction")
print("="*60)

extracted = []
fig_n, tbl_n, alg_n = 1, 1, 1

for grp in all_groups:
    pg = grp[0]["page"]
    page = doc[pg]
    pw, ph = page.rect.width, page.rect.height
    col_mid = get_col_mid(page)
    ref = min(grp, key=lambda c: c["bbox"][1])
    fam = cap_family(ref["kw"])
    num = ref["num"]
    cap_y0 = ref["bbox"][1]
    cap_col = ref.get("col", "left")
    cap_texts = " | ".join(c["text"][:60] for c in grp)

    rect = None

    # Strategy A: Drawing cluster match
    if pg in all_clusters:
        candidates = []
        for c in all_clusters[pg]:
            if c["y1"] > cap_y0: continue
            # Column matching: same column or full-width
            if cap_col != c["col"] and c["col"] != "full" and cap_col != "full":
                continue
            gh = c["y1"] - c["y0"]
            if gh < 25: continue
            candidates.append((cap_y0 - c["y1"], c))

        if candidates:
            candidates.sort(key=lambda x: x[0])
            _, best = candidates[0]
            x0 = max(best["x0"] - 15, page.rect.x0 + 5)
            x1 = min(best["x1"] + 15, page.rect.x1 - 5)
            y0 = best["y0"] - 10
            y1 = min(best["y1"] + 10, cap_y0 - 2)
            if y1 - y0 >= 40:
                rect = fitz.Rect(x0, y0, x1, y1)
                print(f"  P{pg+1} {fam}#{num}: cluster match "
                      f"y=({y0:.0f},{y1:.0f}) h={y1-y0:.0f} col={best['col']} n={best['count']}")

    # Strategy B: Algorithm extraction (page 5)
    if rect is None and fam == "algorithm":
        right_blocks = []
        for b in page.get_text("dict")["blocks"]:
            if b["type"] != 0: continue
            if b["bbox"][0] < col_mid: continue
            lt = []
            for line in b.get("lines", []):
                lt.append("".join(s["text"] for s in line.get("spans", [])))
            right_blocks.append({"bbox": list(b["bbox"]), "text": " ".join(lt)})
        right_blocks.sort(key=lambda b: b["bbox"][1])

        if right_blocks:
            # Algorithm pseudocode ends before the example text or flowchart
            # Find the boundary by looking for the end of numbered steps
            algo_end = None
            for tb in right_blocks:
                text = tb["text"]
                yp = tb["bbox"][1]
                # Example text markers
                if yp > 300 and ("票" in text or "解释" in text or "例子" in text):
                    algo_end = tb["bbox"][1] - 5
                    break
            if algo_end is None:
                # Find the block containing the final algorithm step (return)
                for tb in reversed(right_blocks):
                    text = tb["text"]
                    if "return" in text.lower() or "end" in text.lower():
                        algo_end = tb["bbox"][3] + 5
                        break
            if algo_end is None:
                # Hard fallback: algorithm fills the top half of the right column
                algo_end = page.rect.y0 + page.rect.height * 0.6
            if algo_end and algo_end > 100:
                x0 = col_mid - 12; x1 = pw - 8
                y0 = page.rect.y0 + 25; y1 = algo_end - 3
                rect = fitz.Rect(x0, y0, x1, y1)
                print(f"  P{pg+1} {fam}#{num}: algorithm text y=({y0:.0f},{y1:.0f})")

    # Strategy C: Text-gap fallback
    if rect is None:
        if cap_col == "left": x0, x1 = page.rect.x0 + 8, col_mid + 12
        elif cap_col == "right": x0, x1 = col_mid - 12, pw - 8
        else: x0, x1 = 8, pw - 8

        # Find bottom of last body text cluster above caption
        above_blocks = []
        for b in page.get_text("dict")["blocks"]:
            if b["type"] != 0: continue
            bx0 = b["bbox"][0]
            if cap_col == "left" and bx0 >= col_mid: continue
            if cap_col == "right" and bx0 < col_mid: continue
            if b["bbox"][3] < cap_y0:
                above_blocks.append(list(b["bbox"]))

        y0 = page.rect.y0 + 25
        if above_blocks:
            above_blocks.sort(key=lambda b: b[1])
            # Find chain break above caption
            chain_end_idx = len(above_blocks) - 1
            for i in range(len(above_blocks) - 1, 0, -1):
                gap = above_blocks[i][1] - above_blocks[i-1][3]
                if gap > 25:
                    chain_end_idx = i
                    break
            y0 = above_blocks[chain_end_idx - 1][3] + 3 if chain_end_idx > 0 else y0

        y1 = cap_y0 - 3
        if y1 - y0 >= 60:
            rect = fitz.Rect(x0, y0, x1, y1)
            print(f"  P{pg+1} {fam}#{num}: text-gap y=({y0:.0f},{y1:.0f}) h={y1-y0:.0f}")

    # Strategy D: Table-specific -- content is BELOW the caption
    if rect is None and fam == "table" and pg in all_clusters:
        below = []
        for c in all_clusters[pg]:
            if c["y0"] < cap_y0: continue
            if cap_col != c["col"] and c["col"] != "full" and cap_col != "full": continue
            below.append((c["y0"] - cap_y0, c))
        if below:
            below.sort(key=lambda x: x[0])
            _, best = below[0]
            x0 = max(best["x0"] - 15, page.rect.x0 + 5)
            x1 = min(best["x1"] + 15, page.rect.x1 - 5)
            y0 = cap_y0 - 5
            y1 = best["y1"] + 30
            if y1 - y0 >= 40:
                rect = fitz.Rect(x0, y0, x1, y1)
                print(f"  P{pg+1} {fam}#{num}: table below-caption "
                      f"y=({y0:.0f},{y1:.0f}) h={y1-y0:.0f}")

    if rect is None:
        print(f"  P{pg+1} {fam}#{num}: SKIP")
        continue

    # Overlap check
    overlap = False
    for prev in extracted:
        if prev["page"] != pg: continue
        pr = prev["rect"]
        if rect.y1 > pr.y0 and rect.y0 < pr.y1:
            ol_h = min(rect.y1, pr.y1) - max(rect.y0, pr.y0)
            if ol_h > (rect.y1 - rect.y0) * 0.3:
                overlap = True; break
    if overlap:
        print(f"  P{pg+1} {fam}#{num}: SKIP (overlap)")
        continue

    # Render
    try:
        pad = 5
        clip = fitz.Rect(max(0, rect.x0 - pad), max(0, rect.y0 - pad),
                        min(pw, rect.x1 + pad), min(ph, rect.y1 + pad))
        pix = page.get_pixmap(dpi=200, matrix=fitz.Matrix(200/72, 200/72), clip=clip)

        if fam == "table": name = f"table{tbl_n:02d}.png"; tbl_n += 1
        elif fam == "algorithm": name = f"algo{alg_n:02d}.png"; alg_n += 1
        else: name = f"fig{fig_n:02d}.png"; fig_n += 1

        fpath = os.path.join(assets_dir, name)
        pix.save(fpath)
        extracted.append({"page": pg, "rect": clip, "name": name})
        print(f"  -> SAVED {name} ({pix.width}x{pix.height})")
    except Exception as e:
        print(f"  -> FAILED: {e}")

# Cleanup old temp files
for f in os.listdir(assets_dir):
    fp = os.path.join(assets_dir, f)
    if not os.path.isfile(fp) or f.endswith(".py"): continue
    if f.startswith("auto_fig") or f.startswith("extracted_"):
        os.remove(fp)

doc.close()

# ===== Summary =====
print("\n"+"="*60)
print("FINAL ASSETS")
print("="*60)
for f in sorted(os.listdir(assets_dir)):
    fp = os.path.join(assets_dir, f)
    if not os.path.isfile(fp) or f.endswith(".py"): continue
    sz = os.path.getsize(fp) / 1024
    labels = []
    if re.match(r'^fig\d+\.(png|jpg)$', f): labels.append("FIGURE")
    if re.match(r'^table\d+\.png$', f): labels.append("TABLE")
    if re.match(r'^algo\d+\.png$', f): labels.append("ALGORITHM")
    if f.startswith("page_"): labels.append("PAGE PREVIEW")
    print(f"  {f:40s} {sz:8.1f} KB  {' | '.join(labels)}")

print(f"\nExtracted: {fig_n-1} figures | {tbl_n-1} tables | {alg_n-1} algorithms")
print(f"Raster author photos: 4 (fig01-04.jpg from pdfimages)")
print(f"Page previews: {PAGE_COUNT}")
print(f"Assets: {assets_dir}")
