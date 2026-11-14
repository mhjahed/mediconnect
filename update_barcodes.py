# update_barcodes.py — CREATE this file in project root

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediconnect_project.settings')
django.setup()

from access_control.models import StaffIDCard, PersonalAccessBarcode

print("\n🔄 Updating all ID card barcodes...\n")

count = 0
for card in StaffIDCard.objects.all():
    old_code = card.access_code
    new_code = StaffIDCard.generate_access_code(card.user)

    card.access_code = new_code
    card.barcode_image = None
    card.generate_barcode_image()
    card.save()

    PersonalAccessBarcode.objects.update_or_create(
        user=card.user,
        defaults={'barcode_text': new_code, 'is_active': True}
    )

    print(f"✅ {card.user.get_full_name():30s}  {old_code:20s} → {new_code}")
    count += 1

print(f"\n🎉 {count} cards updated successfully!\n")