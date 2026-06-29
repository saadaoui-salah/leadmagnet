import json
from pathlib import Path
from django.core.management.base import BaseCommand
from properties.models import ZipCode


class Command(BaseCommand):
    help = "Load ZIP code boundaries from geo.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=str(Path(__file__).parent.parent.parent.parent / "geo.json"),
            help="Path to geo.json file",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])

        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        with open(file_path, "r") as f:
            data = json.load(f)

        created = 0
        updated = 0

        for zipcode, bounds in data.items():
            obj, was_created = ZipCode.objects.update_or_create(
                zipcode=zipcode,
                defaults={
                    "south": bounds["south"],
                    "west": bounds["west"],
                    "north": bounds["north"],
                    "east": bounds["east"],
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {len(data)} ZIP codes: {created} created, {updated} updated"
            )
        )
