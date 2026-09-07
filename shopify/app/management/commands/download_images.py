import os
import urllib.request
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from app.models import Product, Category
import ssl


# Disable SSL verification for downloading
ssl._create_default_https_context = ssl._create_unverified_context


PRODUCT_IMAGES = {
    # Technology
    "iPhone 15 Pro": "https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=800&q=80",
    "MacBook Air M3": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&q=80",
    "Samsung Galaxy S24": "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=800&q=80",
    "Sony WH-1000XM5": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80",
    "iPad Pro 12.9": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=800&q=80",
    "Samsung Galaxy Watch 6": "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=800&q=80",

    # Fashion & Sports
    "Nike Air Max 2024": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80",
    "Premium Cotton T-Shirt": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&q=80",
    "Adidas Ultraboost": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=800&q=80",
    "Levi's Denim Jacket": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=800&q=80",
    "Ray-Ban Aviator": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=800&q=80",

    # Music
    "AirPods Pro 2": "https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?w=800&q=80",
    "JBL Flip 6 Speaker": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800&q=80",
    "Fender Acoustic Guitar": "https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=800&q=80",

    # Home
    "IKEA Smart LED Lamp": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800&q=80",
    "Memory Foam Pillow": "https://images.unsplash.com/photo-1631679706909-1844bbd07221?w=800&q=80",
    "Ceramic Plant Pot Set": "https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=800&q=80",
}


class Command(BaseCommand):
    help = "Download real product images"

    def handle(self, *args, **options):
        for title, url in PRODUCT_IMAGES.items():
            try:
                product = Product.objects.filter(title=title).first()
                if not product:
                    self.stdout.write(f"{self.style.WARNING('Not found')}: {title}")
                    continue

                # Skip if already has image
                if product.product_image and product.product_image.name:
                    self.stdout.write(f"{self.style.WARNING('Skipped (has image)')}: {title}")
                    continue

                self.stdout.write(f"Downloading: {title}...")
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, timeout=15) as response:
                    image_data = response.read()

                # Save to product
                filename = f"{title.lower().replace(' ', '_')}.jpg"
                product.product_image.save(filename, ContentFile(image_data), save=True)
                self.stdout.write(f"{self.style.SUCCESS('Saved')}: {title}")
            except Exception as e:
                self.stdout.write(f"{self.style.ERROR(f'Failed {title}')}: {str(e)}")
        self.stdout.write(self.style.SUCCESS("Done!"))
