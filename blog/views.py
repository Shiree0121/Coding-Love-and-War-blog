from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import Http404
from .models import Post, Comment
from .forms import PostForm, RegisterForm, LoginForm, CommentForm

# Create your views here.

def home(request):
    return render(request, 'blog/home.html')


def post_list(request):
    posts = Post.objects.filter(status=1).order_by('-created_on')
    return render(request, 'blog/post_list.html', {'posts': posts})


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status=1)
    comment_form = CommentForm()
    
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
            messages.success(request, 'Your comment has been posted! It will appear once approved.')
            return redirect('post_detail', slug=post.slug)
    
    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comment_form': comment_form
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
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Your post has been created successfully!')
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
            messages.success(request, f'Welcome {user.username}! Your account has been created.')
            return redirect('home')
    else:
        form = RegisterForm()
    
    return render(request, 'blog/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    form = LoginForm(request)
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
    
    return render(request, 'blog/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')
