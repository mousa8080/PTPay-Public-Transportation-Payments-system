import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Aggregate code from specified files into one file'

    def handle(self, *args, **options):
        # جلب قائمة الملفات ومسار الملف الناتج من settings
        files = getattr(settings, 'AGGREGATE_CODE_FILES', [])
        output_path = getattr(settings, 'AGGREGATE_CODE_OUTPUT', 'all_code.txt')

        # افتح (أو أنشئ) الملف الناتج للكتابة
        with open(output_path, 'w', encoding='utf-8') as out_file:
            for rel_path in files:
                abs_path = os.path.join(settings.BASE_DIR, rel_path)
                out_file.write(f'# ===== File: {rel_path} =====\n\n')
                try:
                    with open(abs_path, encoding='utf-8') as f:
                        out_file.write(f.read())
                except FileNotFoundError:
                    out_file.write(f'# Error: file not found: {rel_path}\n')
                out_file.write('\n\n')

        self.stdout.write(self.style.SUCCESS(
            f'✅ Aggregated {len(files)} files into {output_path}'
        ))
