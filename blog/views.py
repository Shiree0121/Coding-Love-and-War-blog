from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils.text import slugify
from .models import Post, Comment
from .forms import PostForm, RegisterForm, LoginForm, CommentForm

# Create your views here.


def home(request):
    posts = Post.objects.filter(status=1, slug__isnull=False).exclude(
        slug='').order_by('-created_on')[:3]
    return render(request, 'blog/home.html', {'posts': posts})


def post_list(request):
    posts = Post.objects.filter(status=1, slug__isnull=False).exclude(
        slug='').order_by('-created_on')
    return render(request, 'blog/post_list.html', {'posts': posts})


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status=1)
    comment_form = CommentForm()

    # Check if user has liked or disliked
    user_has_liked = False
    user_has_disliked = False
    if request.user.is_authenticated:
        user_has_liked = post.likes.filter(id=request.user.id).exists()
        user_has_disliked = post.dislikes.filter(id=request.user.id).exists()

    # Handle comment submission
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, 'You must be logged in to comment.')
            return redirect('login')

        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(
                request,
                'Your comment has been posted! It will appear once approved.')
            return redirect('post_detail', slug=post.slug)

    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comment_form': comment_form,
        'user_has_liked': user_has_liked,
        'user_has_disliked': user_has_disliked,
    })


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
            messages.success(request, 'Your post has been updated!')
            return redirect('post_detail', slug=post.slug)
    else:
        form = PostForm(instance=post)

    return render(request, 'blog/edit_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, slug):
    post = get_object_or_404(Post, slug=slug)

    # Only allow the author to delete their own post
    if request.user != post.author:
        raise Http404("You don't have permission to delete this post.")

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Your post has been deleted.')
        return redirect('post_list')

    return render(request, 'blog/delete_post.html', {'post': post})


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user

            # Generate slug from title
            if not post.title or not post.title.strip():
                messages.error(request, 'Title cannot be empty.')
                return render(request, 'blog/create_post.html', {'form': form})

            base_slug = slugify(post.title)
            if not base_slug:
                messages.error(request, 'Title must contain valid characters.')
                return render(request, 'blog/create_post.html', {'form': form})

            slug = base_slug
            counter = 1

            # Ensure slug is unique
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            post.slug = slug
            post.save()
            messages.success(
                request, 'Your post has been created successfully!')
            return redirect('post_detail', slug=post.slug)
    else:
        form = PostForm()

    return render(request, 'blog/create_post.html', {'form': form})


def home_page_view(request):
    return render(request, 'blog/home.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f'Welcome {user.username}! Your account has been created.')
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'blog/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
    else:
        form = LoginForm(request)

    return render(request, 'blog/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def like_post(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if request.method == 'POST':
        # If user already liked, remove like
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
        else:
            # Add like and remove dislike if exists
            post.likes.add(request.user)
            if post.dislikes.filter(id=request.user.id).exists():
                post.dislikes.remove(request.user)

    return HttpResponseRedirect(reverse('post_detail', args=[slug]))


@login_required
def dislike_post(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if request.method == 'POST':
        # If user already disliked, remove dislike
        if post.dislikes.filter(id=request.user.id).exists():
            post.dislikes.remove(request.user)
        else:
            # Add dislike and remove like if exists
            post.dislikes.add(request.user)
            if post.likes.filter(id=request.user.id).exists():
                post.likes.remove(request.user)

    return HttpResponseRedirect(reverse('post_detail', args=[slug]))


@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    # Only allow the author to edit their own comment
    if request.user != comment.author:
        raise Http404("You don't have permission to edit this comment.")

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            # Reset approval status when edited
            edited_comment = form.save(commit=False)
            edited_comment.approved = False
            edited_comment.save()
            messages.success(
                request,
                'Your comment has been updated and is awaiting approval.')
            return redirect('post_detail', slug=comment.post.slug)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/edit_comment.html',
                  {'form': form, 'comment': comment})


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    # Only allow the author to delete their own comment
    if request.user != comment.author:
        raise Http404("You don't have permission to delete this comment.")

    if request.method == 'POST':
        post_slug = comment.post.slug
        comment.delete()
        messages.success(request, 'Your comment has been deleted.')
        return redirect('post_detail', slug=post_slug)

    return redirect('post_detail', slug=comment.post.slug)
