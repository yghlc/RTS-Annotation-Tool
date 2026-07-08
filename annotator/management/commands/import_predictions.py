import os
import glob
import json
from django.core.management.base import BaseCommand
from annotator.models import H3Cell, Annotation

MODEL_EMAIL = 'model'
SUPER_DATA_DIR = '/hdd10Tb/chenyf/super-data'


class Command(BaseCommand):
    help = '把全部cell导入H3Cell(待审核队列)；有SAM2UNet(经ChangeCLIP过滤)预测结果的cell，把多边形一并导入Annotation表(email=model)'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None, help='只导入前N个cell')

    def handle(self, *args, **options):
        cell_ids = sorted([
            d for d in os.listdir(SUPER_DATA_DIR)
            if os.path.isdir(os.path.join(SUPER_DATA_DIR, d))
        ])

        limit = options.get('limit')
        if limit:
            cell_ids = cell_ids[:limit]

        self.stdout.write(f'共 {len(cell_ids)} 个cell，开始导入...')

        cells_created = 0
        cells_with_predictions = 0
        annotations_written = 0

        for i, cell_id in enumerate(cell_ids):
            cell, created = H3Cell.objects.get_or_create(
                cell_id=cell_id,
                defaults={'order_index': i}
            )
            if created:
                cells_created += 1

            pixel_matches = glob.glob(os.path.join(SUPER_DATA_DIR, cell_id, f'pixel_polygons_id{cell_id}_*.json'))
            if not pixel_matches:
                continue
            pixel_path = pixel_matches[0]
            cells_with_predictions += 1

            with open(pixel_path) as f:
                data = json.load(f)

            for year_str, year_instances in data['years'].items():
                instances = []
                for inst in year_instances:
                    polygon = inst['pixel_polygon']
                    # DB 里的 polygon 是开环（不重复首点），闭合由前端/导出逻辑自己做
                    if len(polygon) > 1 and polygon[0] == polygon[-1]:
                        polygon = polygon[:-1]
                    instances.append({
                        'id': inst['rts_id'],
                        'polygon': polygon,
                    })
                Annotation.objects.update_or_create(
                    cell=cell, email=MODEL_EMAIL, year=int(year_str),
                    defaults={'polygon': instances}
                )
                annotations_written += 1

            if (i + 1) % 500 == 0 or (i + 1) == len(cell_ids):
                self.stdout.write(f'[{i+1}/{len(cell_ids)}] 处理完成')

        self.stdout.write(self.style.SUCCESS(
            f'导入完成：新增 {cells_created} 个H3Cell（共{len(cell_ids)}个），其中 {cells_with_predictions} 个有模型预测，'
            f'写入/更新 {annotations_written} 条Annotation（email={MODEL_EMAIL}）'
        ))
