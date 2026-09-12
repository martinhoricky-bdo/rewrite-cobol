from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Department, Employee
from fleet.models import Airplane, Airport
from legacy_import.services import (
    flush_seed_data,
    seed_crews,
    seed_employees,
    seed_passengers,
    seed_reference_data,
    seed_reference_purchase,
)
from operations.models import Crew, Flight, Shift
from operations.services import generate_seed_flights
from sales.models import Buy, Passenger, Ticket


class Command(BaseCommand):
    help = "Seed development data from the read-only legacy files."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--flush", action="store_true")
        parser.add_argument("--from-date", type=date.fromisoformat, default=None)
        parser.add_argument("--days", type=int, default=60)

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        if options["days"] < 1:
            raise CommandError("--days must be a positive integer")
        start = options["from_date"] or timezone.localdate()
        if isinstance(start, str):
            start = date.fromisoformat(start)
        root = Path(settings.LEGACY_ROOT)
        employee_path = root / "COB-PROG/EMPLO-INSERT/EMPLOYEE-LIST.json"
        passenger_dir = root / "COB-PROG/PASSENGER-INSERT"
        passenger_paths = sorted(passenger_dir.glob("PASSENGER*.xml"))
        for path in (employee_path, passenger_dir):
            if not path.exists():
                raise CommandError(f"Missing legacy file: {path}")
        if not passenger_paths:
            raise CommandError(f"Missing legacy file: {passenger_dir / 'PASSENGER1.xml'}")
        if options["flush"]:
            flush_seed_data()
        seed_reference_data()
        seed_employees(employee_path)
        client = seed_passengers(passenger_paths)
        crews = seed_crews()
        generate_seed_flights(date(2022, 9, 1), 30, crews)
        generate_seed_flights(start, options["days"], crews)
        seed_reference_purchase(client)
        counts = (
            ("dept", Department),
            ("airport", Airport),
            ("airplane", Airplane),
            ("emplo", Employee),
            ("passengers", Passenger),
            ("crew", Crew),
            ("shift", Shift),
            ("flight", Flight),
            ("buy", Buy),
            ("ticket", Ticket),
        )
        for label, model in counts:
            self.stdout.write(f"{label}: {model.objects.count()}")
        self.stdout.write(self.style.SUCCESS("Seed completed"))
