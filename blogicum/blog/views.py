import datetime as dt
from typing import Any

from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.query import QuerySet
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.shortcuts import (get_object_or_404,
                              render, redirect)
from django.contrib.auth import get_user_model
from django.views.generic import (CreateView, DeleteView, UpdateView,
                                  DetailView, ListView)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic.edit import DeletionMixin

from blogicum import constants
from blog.models import Post, Category, Comment
from blog.forms import PostForm, CommentForm, UserForm

User = get_user_model()


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs['slug'],)

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'slug': self.object.username}
        )


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['pk'])
        if instance.author != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'pk': self.object.post_id}
        )


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['pk'])
        if instance.author != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'pk': self.object.post_id}
        )


class PostListView(ListView):
    model = Post
    paginate_by = constants.POSTS_PER_PAGE
    template_name = 'blog/index.html'
    ordering = '-pub_date'

    def get_queryset(self) -> QuerySet[Any]:
        return (super().get_queryset().annotate(
                comment_count=Count('comments')
                ).select_related(
                'category', 'author', 'location'
                ).filter(
                    is_published=True,
                    category__is_published=True,
                    pub_date__lte=dt.datetime.now(dt.timezone.utc),
                ))


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


class PostUpdateView(UpdateView, LoginRequiredMixin):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail', pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'slug': self.object.author}
        )


class PostDeleteView(DeletionMixin, PostUpdateView):
    success_url = reverse_lazy('blog:index')


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = constants.POSTS_PER_PAGE
    ordering = '-pub_date'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )
        return context

    def get_queryset(self) -> QuerySet[Any]:
        return (super().get_queryset().annotate(
                comment_count=Count('comments')
                ).select_related(
                'category', 'author', 'location'
                ).filter(
                    is_published=True,
                    category__is_published=True,
                    pub_date__lte=dt.datetime.now(dt.timezone.utc),
                    category__slug=self.kwargs['category_slug']
                ))


def profile(request, slug):
    profile = get_object_or_404(User, username=slug)
    posts = Post.objects.annotate(
                comment_count=Count('comments')
            ).select_related(
                'category', 'author', 'location'
            ).filter(
                author=profile
            ).order_by('-pub_date')
    paginator = Paginator(posts, constants.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'profile': profile,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', pk=pk)
