"""
把 annotations-train/ 下的 GeoJSON 转换成二值 label 图像
有 RTS = 255，背景 = 0
输出到 labels/<cell_id>/<year>_label.png
"""

import json
import numpy as np
import cv2
from pathlib import Path

ANN_DIR = Path(__file__).parent.parent / 'annotations-train'
OUT_DIR = Path(__file__).parent.parent / 'labels'


def json_to_label(json_path: Path):
    data = json.loads(json_path.read_text())
    features = data.get('features', [])
    if not features:
        return

    # 按年份分组
    by_year = {}
    for feat in features:
        props = feat.get('properties', {})
        year = props.get('year')
        pixel_polygon = props.get('pixel_polygon')
        image_size = props.get('image_size')
        if not year or not pixel_polygon or not image_size:
            continue
        if year not in by_year:
            by_year[year] = {'size': image_size, 'polygons': []}
        by_year[year]['polygons'].append(pixel_polygon)

    cell_id = json_path.parent.name
    for year, info in by_year.items():
        w = info['size']['width']
        h = info['size']['height']
        mask = np.zeros((h, w), dtype=np.uint8)
        for poly in info['polygons']:
            pts = np.array([[p[0], p[1]] for p in poly[:-1]], dtype=np.int32)
            cv2.fillPoly(mask, [pts], 255)

        out_dir = OUT_DIR / cell_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f'{year}_label.png'
        cv2.imwrite(str(out_path), mask)
        print(f'Saved: {out_path}')


if __name__ == '__main__':
    for json_file in ANN_DIR.glob('*/*.json'):
        json_to_label(json_file)
    print('Done.')
