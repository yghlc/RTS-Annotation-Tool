import json
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from annotator.models import CellResult, Annotation
from annotator.views import _build_verified_annotations


class Command(BaseCommand):
    help = '从数据库重新生成所有 verified_annotations/<cell>/<email>.json（新的分组格式），覆盖旧的扁平格式文件'

    def handle(self, *args, **options):
        results = CellResult.objects.filter(result__in=['yes', 'no']).select_related('cell')
        self.stdout.write(f'找到 {results.count()} 条已验证结果(yes/no)，开始重新生成...')

        written = 0
        for cr in results:
            annotations = {}
            for a in Annotation.objects.filter(cell=cr.cell, email=cr.email):
                annotations[str(a.year)] = a.polygon

            verified = _build_verified_annotations(cr.cell.cell_id, annotations)
            verified['validate_result'] = cr.result

            prefix = cr.email.split('@')[0] if '@' in cr.email else cr.email
            folder = Path(settings.BASE_DIR) / 'verified_annotations' / cr.cell.cell_id
            folder.mkdir(parents=True, exist_ok=True)
            out_path = folder / f'{prefix}.json'
            out_path.write_text(json.dumps(verified, ensure_ascii=False, indent=2))
            written += 1

        self.stdout.write(self.style.SUCCESS(f'重新生成完成：{written} 个文件'))
