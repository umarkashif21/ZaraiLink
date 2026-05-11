from django.core.management.base import BaseCommand
from companies.models import Company, KeyContact


DUMMY_CONTACTS = [
    ("Ahmed Raza",     "Sales Manager",        "+92 300 1112233", "+92 300 1112233", "ahmed.raza@example.com"),
    ("Sana Khan",      "Export Coordinator",   "+92 321 4445566", "+92 321 4445566", "sana.khan@example.com"),
    ("Bilal Hussain",  "Procurement Lead",     "+92 333 7778899", "+92 333 7778899", "bilal.hussain@example.com"),
    ("Hira Malik",     "Logistics Officer",    "+92 345 1239876", "+92 345 1239876", "hira.malik@example.com"),
]


class Command(BaseCommand):
    help = "Seed 2 dummy KeyContacts on the first 20 companies (alphabetical). Idempotent — skips companies that already have any KeyContact."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20, help="How many companies to seed (default 20).")
        parser.add_argument("--per-company", type=int, default=2, help="Contacts per company (default 2).")

    def handle(self, *args, **opts):
        limit = opts["limit"]
        per_company = min(opts["per_company"], len(DUMMY_CONTACTS))

        companies = Company.objects.order_by("name")[:limit]
        if not companies:
            self.stdout.write(self.style.ERROR("No companies in DB. Import companies first."))
            return

        created_total = 0
        skipped = 0
        for company in companies:
            if company.key_contacts.exists():
                self.stdout.write(self.style.WARNING(f"Skip (already has contacts): {company.name}"))
                skipped += 1
                continue

            for i in range(per_company):
                name, designation, phone, whatsapp, email = DUMMY_CONTACTS[i]
                # namespace email per-company so it's unique-looking
                slug = "".join(c for c in company.name.lower() if c.isalnum())[:20] or f"co{company.pk}"
                company_email = f"{name.split()[0].lower()}.{slug}@example.com"

                KeyContact.objects.create(
                    company=company,
                    name=name,
                    designation=designation,
                    phone=phone,
                    whatsapp=whatsapp,
                    email=company_email,
                    is_public=False,
                )
                created_total += 1

            self.stdout.write(self.style.SUCCESS(f"Seeded {per_company} contacts → {company.name}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Created {created_total} contacts across {len(companies) - skipped} companies "
            f"({skipped} skipped — already had contacts)."
        ))
