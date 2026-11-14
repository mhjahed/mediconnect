# access_control/management/commands/regenerate_barcodes.py
# Create this file - works every time you need it

from django.core.management.base import BaseCommand
from access_control.models import StaffIDCard, PersonalAccessBarcode


class Command(BaseCommand):
    help = 'Regenerate short access codes and barcode images for all ID cards'

    def handle(self, *args, **options):
        cards = StaffIDCard.objects.all()

        if not cards.exists():
            self.stdout.write(self.style.WARNING('No ID cards found.'))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(f'\n🔄 Regenerating {cards.count()} barcode(s)...\n'))

        for card in cards:
            old_code = card.access_code

            # Generate new short code
            new_code = StaffIDCard.generate_access_code(card.user)
            card.access_code = new_code

            # Clear and regenerate barcode image
            card.barcode_image = None
            card.generate_barcode_image()
            card.save()

            # Update PersonalAccessBarcode (linked to scanner)
            badge, created = PersonalAccessBarcode.objects.update_or_create(
                user=card.user,
                defaults={
                    'barcode_text': new_code,
                    'is_active':    True,
                }
            )

            arrow = '→' if old_code != new_code else '='
            self.stdout.write(self.style.SUCCESS(
                f"✅ {card.user.get_full_name():30s}  {old_code:20s} {arrow} {new_code}"
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\n🎉 Successfully regenerated {cards.count()} barcode(s)!\n'
        ))