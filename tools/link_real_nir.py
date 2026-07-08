"""
把super-data里不可靠的"超分辨率NIR"({year}_nir.png)替换成软链接，
指向TP参考数据集里真实的原始10m NIR影像和逐年GIF动图。

用法：
    python link_real_nir.py
"""

import os
import sys
import glob

SUPER_DATA_DIR = "/hdd10Tb/chenyf/super-data"
TP_DIR = "/home/hlc/Data/rts_ArcticDEM_mapping/result_analysis/valid_json_files_20251222_select_pngs/TP"
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]


def main():
    if len(sys.argv) > 1:
        cell_ids = [sys.argv[1]]
    else:
        cell_ids = sorted([
            d for d in os.listdir(SUPER_DATA_DIR)
            if os.path.isdir(os.path.join(SUPER_DATA_DIR, d))
        ])
    print(f"Total cells in super-data: {len(cell_ids)}")

    linked_png = 0
    missing_tp_cell = 0
    missing_year_png = 0
    linked_gif = 0
    missing_gif = 0

    for i, cell_id in enumerate(cell_ids):
        tp_cell_dir = os.path.join(TP_DIR, cell_id)
        if not os.path.isdir(tp_cell_dir):
            missing_tp_cell += 1
            continue

        sd_cell_dir = os.path.join(SUPER_DATA_DIR, cell_id)

        for year in YEARS:
            matches = glob.glob(os.path.join(tp_cell_dir, f"s2nir_{year}_id{cell_id}_*.png"))
            dst = os.path.join(sd_cell_dir, f"{year}_nir.png")
            if not matches:
                missing_year_png += 1
                continue
            src = matches[0]
            if os.path.islink(dst) or os.path.exists(dst):
                os.remove(dst)
            os.symlink(src, dst)
            linked_png += 1

        gif_matches = glob.glob(os.path.join(tp_cell_dir, f"znGIF_id{cell_id}.gif"))
        gif_dst = os.path.join(sd_cell_dir, "nir.gif")
        if gif_matches:
            if os.path.islink(gif_dst) or os.path.exists(gif_dst):
                os.remove(gif_dst)
            os.symlink(gif_matches[0], gif_dst)
            linked_gif += 1
        else:
            missing_gif += 1

        if (i + 1) % 500 == 0 or (i + 1) == len(cell_ids):
            print(f"[{i+1}/{len(cell_ids)}] processed", flush=True)

    print(f"\nDone.")
    print(f"NIR png symlinked: {linked_png} (missing per-year: {missing_year_png})")
    print(f"NIR gif symlinked: {linked_gif} (missing: {missing_gif})")
    print(f"Cells with no TP match at all: {missing_tp_cell}")


if __name__ == "__main__":
    main()
