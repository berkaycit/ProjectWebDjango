from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Post, Comment, Profile, Like
from .forms import PostForm, CommentForm, SignUpForm, ProfileForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.views.generic import TemplateView, ListView
from django.db.models import Q


def post_list(request):
    posts = Post.objects.filter(yayinlanma_tarihi__lte=timezone.now()).order_by('-yayinlanma_tarihi')
    last_ten_posts = Post.objects.filter(yayinlanma_tarihi__lte=timezone.now()).order_by('-yayinlanma_tarihi')[:10]
    return render(request, 'blog/post_list.html', {'posts': posts, 'last_ten_posts': last_ten_posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    number_of_likes = post.likes.all().count()
    return render(request, 'blog/post_detail.html', {'post': post, 'likes': number_of_likes})

def post_cat(request, pk):
    posts = Post.objects.filter(Q(tur__iexact=pk[0]),
                                Q(yayinlanma_tarihi__lte=timezone.now())
                                ).order_by('-yayinlanma_tarihi')

    last_ten_posts = Post.objects.filter(yayinlanma_tarihi__lte=timezone.now()).order_by('-yayinlanma_tarihi')[:10]
    return render(request, 'blog/post_list.html', {'posts': posts, 'last_ten_posts': last_ten_posts})


@login_required
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.yazar = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})

@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.yazar = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form})

@login_required
def post_draft_list(request):
    posts = Post.objects.filter(yayinlanma_tarihi__isnull=True).order_by('-yaratilma_tarihi')
    return render(request, 'blog/post_draft_list.html', {'posts': posts})

@login_required
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.yayinla()
    return redirect('post_detail', pk=pk)

@login_required
def post_remove(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    return redirect('post_list')

def add_comment_to_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = CommentForm()        
    return render(request, 'blog/add_comment_to_post.html', {'form': form})

@login_required
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.approve()
    return redirect('post_detail', pk=comment.post.pk)

@login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()
    return redirect('post_detail', pk=comment.post.pk)


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            #user.profile.birth_date = form.cleaned_data.get('birth_date')
            user.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)

            return redirect('/')
    else:
        form = SignUpForm()

    return render(request, 'blog/signup.html', {'form': form})


def user_profile(request, profile_id):

    is_following = False

    user = get_object_or_404(User, pk=profile_id)
    profile = get_object_or_404(Profile, user=user)

    if profile in request.user.is_following.all():
        is_following = True

    last_posts = Post.objects.filter(Q(yazar=profile_id),
                                         Q(yayinlanma_tarihi__lte=timezone.now())
                                         ).order_by(('-puan'))[:10]

    return render(request, 'blog/profile.html', {'user': user, 'profile': profile, 'last_posts': last_posts, 'is_following': is_following})


def profile_edit(request, profile_id):
    user = request.user
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            info = form.cleaned_data.get('info')
            avatar = form.cleaned_data['avatar'] #request.POST.get('avatar', None)
            print(form.cleaned_data['avatar'])
            gender = request.POST.get('gender', None)
            profile.info = info
            profile.avatar = avatar
            profile.gender = gender
            profile.save()
            return redirect('user_profile', profile_id=user.pk)
    else:
        form = ProfileForm()

    return render(request, 'blog/profile_edit.html', {'user': user, 'form': form, 'profile': profile})


def post_like(request, article_id):

    try:
        created = Like.objects.get(user=request.user, article_id=article_id)
    except:
        created = None

    #print("kontrol yapildi")

    if not created:
        #print("olusturuldu")
        Like.objects.create(user=request.user, article_id=article_id)
    else:
        #print("silindi")
        created.delete()

    return redirect('post_list')

@login_required
def profile_follow_toggle(request):
    user = request.user
    user_to_toggle = request.POST.get("username")
    profile_ = Profile.objects.get(user__username__iexact=user_to_toggle)

    if user in profile_.followers.all(): #bir kişiyi takip ediyorsa zaten
        profile_.followers.remove(user) #listeden çıkar
    else: #takip etmiyorsa
        profile_.followers.add(user) #listeye ekle

    #print(user_to_toggle)
    return redirect('user_profile', profile_id=profile_.user.pk)

def report(request):
    return render(request, 'blog/report.html')