"""
把 pixel_polygons.json（像素坐标）+ geo_meta.json（该cell的地理配准信息）
转换成带真实经纬度的 GeoJSON，供 QGIS / 网页地图查看。

投影公式跟 annotator/views.py 里的 _pixel_to_lonlat 完全一致（NSIDC 极地投影反算），
保证跟现有系统导出的经纬度结果一致。

用法：
    python pixel_to_geojson.py                  # 处理所有 cell
    python pixel_to_geojson.py <cell_id>        # 只处理一个 cell
"""

import os
import sys
import json
import math

FILTERED_DIR = "/hdd10Tb/chenyf/SAM2UNet/predictions/superdata_filtered"


def _pixel_to_lonlat(col, row, gt):
    """与 annotator/views.py 的 _pixel_to_lonlat 保持一致（NSIDC 极地投影反算）"""
    x = gt[0] + col * gt[1] + row * gt[2]
    y = gt[3] + col * gt[4] + row * gt[5]
    a = 6378137.0
    e = 0.0818191908426
    phi_c = math.radians(70)
    lam_0 = math.radians(-45)
    sin_phi_c = math.sin(phi_c)
    t_c = math.tan(math.pi / 4 - phi_c / 2) / ((1 - e * sin_phi_c) / (1 + e * sin_phi_c)) ** (e / 2)
    m_c = math.cos(phi_c) / math.sqrt(1 - e * e * sin_phi_c * sin_phi_c)
    rho = math.sqrt(x * x + y * y)
    if rho == 0:
        return [math.degrees(lam_0), 90.0]
    t = rho * t_c / (a * m_c)
    phi = math.pi / 2 - 2 * math.atan(t)
    for _ in range(10):
        s = math.sin(phi)
        phi = math.pi / 2 - 2 * math.atan(t * ((1 - e * s) / (1 + e * s)) ** (e / 2))
    lam = lam_0 + math.atan2(x, -y)
    return [round(math.degrees(lam), 7), round(math.degrees(phi), 7)]


def convert_one(cell_id):
    cell_dir = os.path.join(FILTERED_DIR, cell_id)
    pixel_path = os.path.join(cell_dir, "pixel_polygons.json")
    geo_meta_path = os.path.join(cell_dir, "geo_meta.json")

    if not (os.path.exists(pixel_path) and os.path.exists(geo_meta_path)):
        return None

    with open(pixel_path) as f:
        pixel_data = json.load(f)
    with open(geo_meta_path) as f:
        geo_meta = json.load(f)

    gt = geo_meta["geotransform"]

    out_features = []
    for feat in pixel_data["features"]:
        props = feat["properties"]
        pixel_polygon = props["pixel_polygon"]
        coords = [_pixel_to_lonlat(p[0], p[1], gt) for p in pixel_polygon]
        out_features.append({
            "type": "Feature",
            "properties": props,
            "geometry": {"type": "Polygon", "coordinates": [coords]},
        })

    out_geojson = {"type": "FeatureCollection", "features": out_features}
    out_path = os.path.join(cell_dir, "model_prediction.geojson")
    with open(out_path, "w") as f:
        json.dump(out_geojson, f, indent=2)
    return len(out_features)


def main():
    if len(sys.argv) > 1:
        cell_ids = [sys.argv[1]]
    else:
        cell_ids = sorted([
            d for d in os.listdir(FILTERED_DIR)
            if os.path.isdir(os.path.join(FILTERED_DIR, d))
        ])

    written = 0
    total_features = 0
    for i, cell_id in enumerate(cell_ids):
        n = convert_one(cell_id)
        if n is None:
            continue
        written += 1
        total_features += n
        if (i + 1) % 500 == 0 or (i + 1) == len(cell_ids):
            print(f"[{i+1}/{len(cell_ids)}] processed", flush=True)

    print(f"\nDone. model_prediction.geojson written for {written} cells, {total_features} total features")


if __name__ == "__main__":
    main()
