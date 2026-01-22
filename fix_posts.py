#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from blog.models import Post
from django.utils.text import slugify

# Fix all posts that have empty or null slugs
posts = Post.objects.filter(slug__isnull=True) | Post.objects.filter(slug='')

for post in posts:
    if post.title:
        base_slug = slugify(post.title)
        slug = base_slug
        counter = 1
        
        # Ensure slug is unique
        while Post.objects.filter(slug=slug).exclude(id=post.id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        post.slug = slug
        post.save()
        print(f"Fixed: {post.title} -> {post.slug}")
    else:
        print(f"Cannot fix post {post.id}: no title")

print("Done!")
