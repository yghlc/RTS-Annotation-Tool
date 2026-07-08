"""
把过滤后（SAM2UNet预测 x ChangeCLIP变化区域有重叠）的 mask 转成像素坐标多边形，
按 cell_id 拆分成一个文件一个（pixel_polygons_id{cell_id}_{suffix}.json），存到
super-data 对应cell文件夹下，不含经纬度、不含image_size（跟geo_meta放一起，不用重复存）。
同一个滑塌体跨年份复用同一个 rts_id（rts01, rts02, ...），靠逐年 mask 重叠做简单追踪。

输出格式（按cell_id分组一次，再按年份分组，同年多个实例放一个列表里）：
    {
      "cell_id": "...",
      "years": {
        "2020": [{"rts_id": "rts01", "pixel_polygon": [[x,y],...]}, ...],
        "2021": [...]
      }
    }

用法：
    python export_pixel_polygons.py
"""

import os
import csv
import glob
import json
import numpy as np
import cv2
from collections import defaultdict

FILTERED_CSV = "/hdd10Tb/chenyf/SAM2UNet/predictions/superdata_full_run/filtered_by_changeclip.csv"
SUPER_DATA_DIR = "/hdd10Tb/chenyf/super-data"
SAM2UNET_MASK_DIR = SUPER_DATA_DIR  # mask 已经统一整合到 super-data 下，命名是 label_{year}_id{cell_id}_{suffix}.png
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]


def find_suffix(cell_id):
    """suffix跟TP原始数据集里的编号一致，从这个cell已有的label文件名里读出来"""
    matches = glob.glob(os.path.join(SUPER_DATA_DIR, cell_id, f"label_*_id{cell_id}_*.png"))
    if not matches:
        return None
    return os.path.basename(matches[0]).rsplit("_", 1)[-1].split(".")[0]
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
    total_instances = 0

    for i, (cell_id, year_rows) in enumerate(sorted(by_cell.items())):
        suffix = find_suffix(cell_id)
        if suffix is None:
            continue
        years_out = {}
        # rts_id -> 最后一次见到它时的mask。这个登记表跨年份持续存在、只增不丢，
        # 不会因为某一年没匹配上（中间断档，或者被无关的误检占用）就把之前的记录冲掉，
        # 保证像"2019识别到、2020没识别到、2021又识别到"这种情况还能对回同一个编号。
        active_instances = {}
        next_instance_num = 1

        for year in YEARS:
            if year not in year_rows:
                continue
            mask_path = os.path.join(SAM2UNET_MASK_DIR, cell_id, f"label_{year}_id{cell_id}_{suffix}.png")
            if not os.path.exists(mask_path):
                continue
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            mask_bin = mask > 127

            blobs = mask_to_polygons(mask_bin)
            year_instances = []
            used_ids_this_year = set()  # 避免同一年内两个不同的斑块抢到同一个编号

            for blob in blobs:
                blob_mask = blob["blob_mask"]
                matched_id = None
                best_overlap = 0
                for rts_id, prev_mask in active_instances.items():
                    if rts_id in used_ids_this_year:
                        continue
                    overlap = int(np.logical_and(blob_mask > 0, prev_mask > 0).sum())
                    if overlap > best_overlap:
                        best_overlap = overlap
                        matched_id = rts_id

                if matched_id is not None:
                    rts_id = matched_id
                else:
                    rts_id = f"rts{next_instance_num:02d}"
                    next_instance_num += 1

                active_instances[rts_id] = blob_mask  # 更新/新增，不清空其他已登记的实例
                used_ids_this_year.add(rts_id)
                year_instances.append({"rts_id": rts_id, "pixel_polygon": blob["pixel_polygon"]})

            if year_instances:
                years_out[str(year)] = year_instances

        if not years_out:
            continue

        out_dir = os.path.join(SUPER_DATA_DIR, cell_id)
        out_path = os.path.join(out_dir, f"pixel_polygons_id{cell_id}_{suffix}.json")
        with open(out_path, "w") as f:
            json.dump({"cell_id": cell_id, "years": years_out}, f, indent=2)

        written += 1
        total_instances += sum(len(v) for v in years_out.values())

        if (i + 1) % 500 == 0 or (i + 1) == len(by_cell):
            print(f"[{i+1}/{len(by_cell)}] processed", flush=True)

    print(f"\nDone. pixel_polygons.json written for {written} cells, {total_instances} total instance-year entries")


if __name__ == "__main__":
    main()
