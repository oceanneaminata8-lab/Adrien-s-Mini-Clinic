import sqlite3
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create a consistent timestamped backup of the clinic SQLite database.'

    def handle(self, *args, **options):
        database = settings.DATABASES['default']
        if database['ENGINE'] != 'django.db.backends.sqlite3':
            raise CommandError('This command currently supports SQLite databases only.')

        source_path = Path(database['NAME'])
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(exist_ok=True)
        target_path = backup_dir / f'clinic-{datetime.now():%Y%m%d-%H%M%S}.sqlite3'

        with sqlite3.connect(source_path) as source, sqlite3.connect(target_path) as target:
            source.backup(target)

        self.stdout.write(self.style.SUCCESS(f'Backup created: {target_path}'))
