from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from django.db.models import Q
from trade_data.models import Transaction
from companies.models import Company


class Command(BaseCommand):
    help = "Backfill Company table from existing Transactions safely"

    def handle(self, *args, **options):

        created_count = 0
        updated_count = 0
        processed = 0

        self.stdout.write(self.style.WARNING("Starting Trade Company Repair..."))

        with db_transaction.atomic():

            transactions = Transaction.objects.all().iterator()

            for tx in transactions:
                processed += 1

                buyer_name = (tx.buyer or "").strip()
                seller_name = (tx.seller or "").strip()

                if not buyer_name and not seller_name:
                    continue

                if tx.trade_type == "IMPORT":
                    buyer_country = tx.destination_country
                    seller_country = tx.origin_country
                else:  # EXPORT
                    seller_country = tx.origin_country
                    buyer_country = tx.destination_country

                if buyer_name:

                    buyer_obj, created = Company.objects.get_or_create(
                        name=buyer_name,
                        defaults={
                            "country": buyer_country or "Unknown",
                            "has_trade_data": True,
                            "is_directory_profile": False,
                        },
                    )

                    if created:
                        created_count += 1
                    else:
                        updated = False

                        if not buyer_obj.country or buyer_obj.country == "Unknown":
                            buyer_obj.country = buyer_country or "Unknown"
                            updated = True

                        if not buyer_obj.has_trade_data:
                            buyer_obj.has_trade_data = True
                            updated = True

                        if updated:
                            buyer_obj.save()
                            updated_count += 1

                if seller_name:

                    seller_obj, created = Company.objects.get_or_create(
                        name=seller_name,
                        defaults={
                            "country": seller_country or "Unknown",
                            "has_trade_data": True,
                            "is_directory_profile": False,
                        },
                    )

                    if created:
                        created_count += 1
                    else:
                        updated = False

                        if not seller_obj.country or seller_obj.country == "Unknown":
                            seller_obj.country = seller_country or "Unknown"
                            updated = True

                        if not seller_obj.has_trade_data:
                            seller_obj.has_trade_data = True
                            updated = True

                        if updated:
                            seller_obj.save()
                            updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Repair Complete.\n"
            f"Transactions processed: {processed}\n"
            f"Companies created: {created_count}\n"
            f"Companies updated: {updated_count}"
        ))