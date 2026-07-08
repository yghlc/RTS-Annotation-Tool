"""
从 super-data 里每个 cell 的 tif 提取轻量地理元数据（geotransform + 尺寸 + EPSG），
写入到该 cell 文件夹下的 geo_meta_id{cell_id}_{suffix}.json（suffix跟TP原始数据集
里的编号一致）。同一个 cell 的 6 个年份 geotransform 基本一致（验证过，浮点误差在
纳米级），所以每个 cell 只存一份，不分年份。

用法：
    python extract_geo_meta.py
"""

import os
import glob
import json
from osgeo import gdal, osr

gdal.UseExceptions()

SUPER_DATA_DIR = "/hdd10Tb/chenyf/super-data"
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]


def extract_one(cell_id):
    cell_dir = os.path.join(SUPER_DATA_DIR, cell_id)
    tif_path = None
    suffix = None
    for year in YEARS:
        matches = glob.glob(os.path.join(cell_dir, f"s2_super_{year}_id{cell_id}_*.tif"))
        if matches:
            tif_path = matches[0]
            suffix = os.path.basename(tif_path).rsplit("_", 1)[-1].split(".")[0]
            break
    if tif_path is None:
        return None, None

    ds = gdal.Open(tif_path)
    gt = ds.GetGeoTransform()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(ds.GetProjection())
    epsg = srs.GetAuthorityCode(None)

    meta = {
        "cell_id": cell_id,
        "width": ds.RasterXSize,
        "height": ds.RasterYSize,
        "geotransform": list(gt),
        "epsg": int(epsg) if epsg else None,
    }
    return meta, suffix


def main():
    cell_ids = sorted([
        d for d in os.listdir(SUPER_DATA_DIR)
        if os.path.isdir(os.path.join(SUPER_DATA_DIR, d))
    ])
    print(f"Found {len(cell_ids)} cells total in super-data")

    written = 0
    missing = 0
    for i, cell_id in enumerate(cell_ids):
        meta, suffix = extract_one(cell_id)
        if meta is None:
            print(f"⚠️ {cell_id}: no tif found, skipping")
            missing += 1
            continue

        out_dir = os.path.join(SUPER_DATA_DIR, cell_id)
        out_path = os.path.join(out_dir, f"geo_meta_id{cell_id}_{suffix}.json")
        with open(out_path, "w") as f:
            json.dump(meta, f, indent=2)
        written += 1

        if (i + 1) % 500 == 0 or (i + 1) == len(cell_ids):
            print(f"[{i+1}/{len(cell_ids)}] processed", flush=True)

    print(f"\nDone. geo_meta_id{{cell_id}}_{{suffix}}.json written for {written} cells, {missing} missing tif")


if __name__ == "__main__":
    main()
