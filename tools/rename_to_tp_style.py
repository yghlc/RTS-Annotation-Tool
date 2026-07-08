"""
把 super-data 下面的简化命名，改成跟 TP 原始数据集风格一致、但加了 "_super"
区分我们自己的超分辨率产物和TP原始10m影像的命名：

    {year}_sr.png/.tif/.webp   ->  s2_super_{year}_id{cell_id}_{suffix}.png/.tif/.webp
    {year}_nir.png/.webp       ->  s2nir_super_{year}_id{cell_id}_{suffix}.png/.webp
    {year}_label.png           ->  label_{year}_id{cell_id}_{suffix}.png
    geo_meta.json              ->  geo_meta_id{cell_id}_{suffix}.json
    pixel_polygons.json        ->  pixel_polygons_id{cell_id}_{suffix}.json

suffix 从 TP 目录里同一个 cell 的文件名里直接读出来（每个cell固定一个数字，
六个年份、以及跟年份无关的geo_meta/pixel_polygons都共用同一个suffix）。

顺便清掉过渡阶段留下的、现在没人用的 nir.gif 软链接。

用法：
    python rename_to_tp_style.py            # 全量执行
    python rename_to_tp_style.py --dry-run  # 只报告，不实际改文件
"""

import os
import re
import sys

SUPER_DATA_DIR = "/hdd10Tb/chenyf/super-data"
TP_DIR = "/home/hlc/Data/rts_ArcticDEM_mapping/result_analysis/valid_json_files_20251222_select_pngs/TP"
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]

SUFFIX_RE = re.compile(r"^s2_\d{4}_id[0-9a-f]+_(\d+)\.png$")


def find_suffix(cell_id):
    tp_cell_dir = os.path.join(TP_DIR, cell_id)
    if not os.path.isdir(tp_cell_dir):
        return None
    for fn in os.listdir(tp_cell_dir):
        m = SUFFIX_RE.match(fn)
        if m:
            return m.group(1)
    return None


def _rename(old_path, new_path, dry_run, counter):
    if not os.path.exists(old_path):
        return
    if os.path.exists(new_path):
        return
    if not dry_run:
        os.rename(old_path, new_path)
    counter[0] += 1


def main():
    dry_run = "--dry-run" in sys.argv

    cell_ids = sorted([
        d for d in os.listdir(SUPER_DATA_DIR)
        if os.path.isdir(os.path.join(SUPER_DATA_DIR, d))
    ])
    print(f"Total cells in super-data: {len(cell_ids)}")

    renamed_files = [0]
    cells_touched = 0
    missing_suffix = 0
    gif_removed = 0

    for i, cell_id in enumerate(cell_ids):
        cell_dir = os.path.join(SUPER_DATA_DIR, cell_id)
        suffix = find_suffix(cell_id)
        if suffix is None:
            missing_suffix += 1
            continue

        before = renamed_files[0]

        for year in YEARS:
            for old_prefix, new_prefix, exts in (
                ("sr", "s2_super", ["png", "tif", "webp"]),
                ("nir", "s2nir_super", ["png", "webp"]),
            ):
                for ext in exts:
                    old_path = os.path.join(cell_dir, f"{year}_{old_prefix}.{ext}")
                    new_path = os.path.join(cell_dir, f"{new_prefix}_{year}_id{cell_id}_{suffix}.{ext}")
                    _rename(old_path, new_path, dry_run, renamed_files)

            old_label = os.path.join(cell_dir, f"{year}_label.png")
            new_label = os.path.join(cell_dir, f"label_{year}_id{cell_id}_{suffix}.png")
            _rename(old_label, new_label, dry_run, renamed_files)

        old_geo = os.path.join(cell_dir, "geo_meta.json")
        new_geo = os.path.join(cell_dir, f"geo_meta_id{cell_id}_{suffix}.json")
        _rename(old_geo, new_geo, dry_run, renamed_files)

        old_pp = os.path.join(cell_dir, "pixel_polygons.json")
        new_pp = os.path.join(cell_dir, f"pixel_polygons_id{cell_id}_{suffix}.json")
        _rename(old_pp, new_pp, dry_run, renamed_files)

        gif_path = os.path.join(cell_dir, "nir.gif")
        if os.path.islink(gif_path) or os.path.exists(gif_path):
            if not dry_run:
                os.remove(gif_path)
            gif_removed += 1

        if renamed_files[0] > before:
            cells_touched += 1

        if (i + 1) % 1000 == 0 or (i + 1) == len(cell_ids):
            print(f"[{i+1}/{len(cell_ids)}] processed", flush=True)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Done.")
    print(f"cells touched: {cells_touched}")
    print(f"files renamed: {renamed_files[0]}")
    print(f"cells missing TP suffix (left untouched): {missing_suffix}")
    print(f"stray nir.gif symlinks removed: {gif_removed}")


if __name__ == "__main__":
    main()
