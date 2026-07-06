"""
把过滤后（SAM2UNet预测 x ChangeCLIP变化区域有重叠）的 mask 转成像素坐标多边形，
按 cell_id 拆分成一个文件一个（pixel_polygons.json），不含经纬度。
同一个滑塌体跨年份复用同一个 id（rts01, rts02, ...），靠逐年 mask 重叠做简单追踪。

用法：
    python export_pixel_polygons.py
"""

import os
import csv
import json
import numpy as np
import cv2
from collections import defaultdict

SAM2UNET_MASK_DIR = "/hdd10Tb/chenyf/SAM2UNet/predictions/superdata_full_run"
FILTERED_CSV = "/hdd10Tb/chenyf/SAM2UNet/predictions/superdata_full_run/filtered_by_changeclip.csv"
FILTERED_DIR = "/hdd10Tb/chenyf/SAM2UNet/predictions/superdata_filtered"
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]
SIMPLIFY_EPSILON_PX = 1.5
MIN_CONTOUR_AREA_PX = 9  # drop tiny noise blobs (<= 3x3 px)


def mask_to_polygons(mask_bin):
    """Extract simplified pixel-space polygons + a small per-blob mask for overlap tracking."""
    contours, _ = cv2.findContours(mask_bin.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    blobs = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < MIN_CONTOUR_AREA_PX:
            continue
        simplified = cv2.approxPolyDP(cnt, SIMPLIFY_EPSILON_PX, True)
        pts = simplified.reshape(-1, 2)
        if len(pts) < 3:
            continue
        pixel_polygon = [[int(p[0]), int(p[1])] for p in pts]
        pixel_polygon.append(pixel_polygon[0])  # close ring

        blob_mask = np.zeros_like(mask_bin, dtype=np.uint8)
        cv2.drawContours(blob_mask, [cnt], -1, 1, thickness=-1)
        blobs.append({"pixel_polygon": pixel_polygon, "blob_mask": blob_mask})
    return blobs


def main():
    with open(FILTERED_CSV) as f:
        rows = [r for r in csv.DictReader(f) if r["kept"] == "True"]

    by_cell = defaultdict(dict)
    for r in rows:
        by_cell[r["id"]][int(r["year"])] = r

    print(f"Cells with kept predictions: {len(by_cell)}")

    written = 0
    total_features = 0

    for i, (cell_id, year_rows) in enumerate(sorted(by_cell.items())):
        features = []
        active_instances = {}  # id_name -> last blob_mask
        next_instance_num = 1

        for year in YEARS:
            if year not in year_rows:
                continue
            mask_path = os.path.join(SAM2UNET_MASK_DIR, cell_id, f"{year}_pred_mask.png")
            if not os.path.exists(mask_path):
                continue
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            mask_bin = mask > 127
            h, w = mask_bin.shape

            blobs = mask_to_polygons(mask_bin)
            new_active = {}

            for blob in blobs:
                blob_mask = blob["blob_mask"]
                matched_id = None
                best_overlap = 0
                for inst_id, prev_mask in active_instances.items():
                    overlap = int(np.logical_and(blob_mask > 0, prev_mask > 0).sum())
                    if overlap > best_overlap:
                        best_overlap = overlap
                        matched_id = inst_id

                if matched_id is not None and matched_id not in new_active:
                    inst_id = matched_id
                else:
                    inst_id = f"rts{next_instance_num:02d}"
                    next_instance_num += 1

                new_active[inst_id] = blob_mask

                features.append({
                    "type": "Feature",
                    "properties": {
                        "id": inst_id,
                        "year": year,
                        "cell_id": cell_id,
                        "pixel_polygon": blob["pixel_polygon"],
                        "image_size": {"width": w, "height": h},
                        "source": "SAM2UNet_filtered_by_ChangeCLIP",
                    },
                })

            active_instances = new_active

        if not features:
            continue

        out_dir = os.path.join(FILTERED_DIR, cell_id)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "pixel_polygons.json")
        with open(out_path, "w") as f:
            json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)

        written += 1
        total_features += len(features)

        if (i + 1) % 500 == 0 or (i + 1) == len(by_cell):
            print(f"[{i+1}/{len(by_cell)}] processed", flush=True)

    print(f"\nDone. pixel_polygons.json written for {written} cells, {total_features} total polygon features")


if __name__ == "__main__":
    main()
