"""
把分散在 SAM2UNet/ChangeCLIP 项目目录下的衍生结果，统一整合到 super-data 各自的cell文件夹下：
- geo_meta.json          (地理配准元数据，全部7428个cell)
- pixel_polygons.json    (像素坐标多边形，只有通过ChangeCLIP过滤、真正有保留结果的cell才有)
- {year}_label.png       (SAM2UNet每年的预测mask，全部7428个cell、6年全部拷贝，不管过滤结果)

用法：
    python consolidate_to_superdata.py
"""

import os
import shutil

SUPER_DATA_DIR = "/hdd10Tb/chenyf/super-data"
FILTERED_DIR = "/hdd10Tb/chenyf/SAM2UNet/predictions/superdata_filtered"
SAM2UNET_FULL_RUN_DIR = "/hdd10Tb/chenyf/SAM2UNet/predictions/superdata_full_run"
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]


def main():
    cell_ids = sorted([
        d for d in os.listdir(FILTERED_DIR)
        if os.path.isdir(os.path.join(FILTERED_DIR, d))
    ])
    print(f"Consolidating {len(cell_ids)} cells (all) into {SUPER_DATA_DIR}")

    copied_geo_meta = 0
    copied_pixel_polygons = 0
    copied_labels = 0
    missing_labels = 0

    for i, cell_id in enumerate(cell_ids):
        src_dir = os.path.join(FILTERED_DIR, cell_id)
        dst_dir = os.path.join(SUPER_DATA_DIR, cell_id)
        os.makedirs(dst_dir, exist_ok=True)

        geo_meta_src = os.path.join(src_dir, "geo_meta.json")
        if os.path.exists(geo_meta_src):
            shutil.copy2(geo_meta_src, os.path.join(dst_dir, "geo_meta.json"))
            copied_geo_meta += 1

        pixel_polygons_src = os.path.join(src_dir, "pixel_polygons.json")
        if os.path.exists(pixel_polygons_src):
            shutil.copy2(pixel_polygons_src, os.path.join(dst_dir, "pixel_polygons.json"))
            copied_pixel_polygons += 1

        for year in YEARS:
            mask_src = os.path.join(SAM2UNET_FULL_RUN_DIR, cell_id, f"{year}_pred_mask.png")
            if os.path.exists(mask_src):
                shutil.copy2(mask_src, os.path.join(dst_dir, f"{year}_label.png"))
                copied_labels += 1
            else:
                missing_labels += 1

        if (i + 1) % 500 == 0 or (i + 1) == len(cell_ids):
            print(f"[{i+1}/{len(cell_ids)}] processed", flush=True)

    print(f"\nDone.")
    print(f"geo_meta.json copied: {copied_geo_meta}")
    print(f"pixel_polygons.json copied: {copied_pixel_polygons}")
    print(f"{{year}}_label.png copied: {copied_labels} (missing: {missing_labels})")


if __name__ == "__main__":
    main()
