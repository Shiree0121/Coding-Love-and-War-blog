"""
Script to fix posts with missing slugs.
Run this with: python manage.py shell < fix_slugs.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils.text import slugify
from blog.models import Post

posts_without_slugs = Post.objects.filter(slug='')
print(f"Found {posts_without_slugs.count()} posts without slugs")

for post in posts_without_slugs:
    # Generate slug from title
    base_slug = slugify(post.title)
    slug = base_slug
    counter = 1
    
    # Ensure slug is unique
    while Post.objects.filter(slug=slug).exclude(id=post.id).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    post.slug = slug
    post.save()
    print(f"Fixed post '{post.title}' - slug: {slug}")

print("Done!")
