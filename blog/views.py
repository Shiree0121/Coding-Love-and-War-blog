from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404
from .models import Post
from .forms import PostForm

# Create your views here.

def post_list(request):
    posts = Post.objects.filter(status=1).order_by('-created_on')
    return render(request, 'blog/post_list.html', {'posts': posts})


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status=1)
    return render(request, 'blog/post_detail.html', {'post': post})


@login_required
def edit_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    
    # Only allow the author to edit their own posts
    if request.user != post.author:
        raise Http404("You don't have permission to edit this post.")
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('post_detail', slug=post.slug)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'blog/edit_post.html', {'form': form, 'post': post})
