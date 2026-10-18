import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from concierge.directory import DATA_PATH
from concierge.models import DirectoryCompany, DirectoryPerson


class Command(BaseCommand):
    help = "Load the CDMO Live attendee directory JSON (built by scripts/build_cdmo_directory.py) into the database."

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?', default=str(DATA_PATH))

    def handle(self, *args, **opts):
        path = Path(opts['path'])
        if not path.exists():
            raise CommandError(f'{path} not found')
        raw = json.loads(path.read_text())
        companies = [DirectoryCompany(key=k, name=c.get('name') or '', segment=c.get('segment', ''), domain=c.get('domain', ''),
                                      modalities=c.get('modalities', []), exhibitor=c.get('exhibitor', False))
                     for k, c in raw['companies'].items()]
        people = [DirectoryPerson(id=p['id'], name=p['name'], title=p.get('title', ''), company_id=p['company'],
                                  email=p.get('email', ''), linkedin=p.get('linkedin', '')) for p in raw['people']]
        DirectoryCompany.objects.bulk_create(companies, update_conflicts=True, unique_fields=['key'],
                                             update_fields=['name', 'segment', 'domain', 'modalities', 'exhibitor'])
        DirectoryPerson.objects.bulk_create(people, update_conflicts=True, unique_fields=['id'],
                                            update_fields=['name', 'title', 'company', 'email', 'linkedin'])
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(companies)} companies, {len(people)} people.'))
