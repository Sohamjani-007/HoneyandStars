from django.http import Http404
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
from django.contrib.postgres.search import SearchVector
from django.contrib.postgres.search import TrigramSimilarity
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect

import threading

LOCK = threading.Lock()


# Create your views here.
def post_list(request, tag_slug=None):
    post_obj = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_obj = post_obj.filter(tags__in=[tag])
    # Pagination with 3 posts per page
    paginator = Paginator(post_obj, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        # If page_number is out of range deliver last page of results
        posts = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        # If page_number is not an integer deliver the first page
        posts = paginator.page(1)
    return render(request,
                  'blog/post/list.html',
                  {'posts': posts, 'tag': tag})


class PostListView(ListView):
    """
    Alternative post list view
    """
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_detail(request, year, month, day, post):
    """
    In shell, try this. Django does the reverse relationship query for us.
    In [14]: post = Post.objects.filter(status=Post.Status.PUBLISHED).last()
    In [15]: post.comments
    Out[15]: <django.db.models.fields.related_descriptors.create_reverse_many_to_one_manager.<locals>.RelatedManager at 0x7f2196779460>
    """
    try:
        post = get_object_or_404(Post,
                                 status=Post.Status.PUBLISHED,
                                 slug=post,
                                 publish__year=year,
                                 publish__month=month,
                                 publish__day=day
                                 )
        # List of active comments for this post
        # How this below query works ? Read doc_string
        comments = post.comments.filter(active=True)
        # Form for users to comment
        form = CommentForm()

        # List of similar posts
        post_tags_ids = post.tags.values_list('id', flat=True)
        similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
        similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    except Post.DoesNotExist:
        raise Http404("No Post found.")
    return render(request, 'blog/post/detail.html', {'post': post, "comments": comments, "form": form,
                                                     'similar_posts': similar_posts})


def post_share(request, post_id):
    """
    :param request:
    :param post_id:
    :return:
    a view to create an instance of the
    form and handle the form submission.
    """
    # Retrieve post by id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False

    if request.method == 'POST':
        import pdb;pdb.set_trace()
        # Form was submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form fields passed validation
            cd = form.cleaned_data
            # If your form data does not validate, cleaned_data will contain only the valid fields.
            # ... send email
            post_url = request.build_absolute_uri(
                post.get_absolute_url())
            subject = f"{cd['name']} recommends you read this fabulous article :<-->:" \
                      f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'sohamjani007@gmail.com',
                      [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})







@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    # A comment was posted
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Create a Comment object without saving it to the database
        comment = form.save(commit=False)
        # Assign the post to the comment
        comment.post = post
        # Save the comment to the database
        # The save() method is available for ModelForm but not for Form instances since
        # they are not linked to any model.
        comment.save()
    return render(request, 'blog/post/comment.html', {'post': post, 'form': form, 'comment': comment})


def post_search(request):
    """
    This POST API is to Search based on the blogs with relevant names in blog.
    Which is searched throughout the title and body in the blog.
    When someone Search, they can easily find the blog which contains that word and also based on number of times used.
    ________________________
    In the preceding code, we apply different weights to the search vectors built using the title and body
    fields. The default weights are D, C, B, and A, and they refer to the numbers 0.1, 0.2, 0.4, and 1.0,
    respectively. We apply a weight of 1.0 to the title search vector (A) and a weight of 0.4 to the body
    vector (B). Title matches will prevail over body contfrom django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.shortcuts import render, redirectent matches. We filter the results to display only
    the ones with a rank higher than 0.3.
    """
    form = SearchForm()
    query = None
    results = []

    if "query" in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B') # config='spanish'
            search_query = SearchQuery(query) # config='spanish'
            results = Post.published.annotate(
                similarity=TrigramSimilarity('title', query), rank=SearchRank(search_vector, search_query)
            ).filter(similarity__gt=0.1).order_by('-rank', '-similarity') # .filter(rank__gt=0.3) # A trigram is a group of three consecutive characters.
    return render(request,
                   'blog/post/search.html',
                   {'form': form,
                   'query': query,
                   'results': results})


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('post_list')
    else:
        form = UserCreationForm()
    return render(request, 'blog/signup_form.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('post_list')
    else:
        form = AuthenticationForm()
    return render(request, 'blog/login_form.html', {'form': form})












class ParallelRequestAPIView(APIView):
    """
    Implementation to Handle Parallel Request.
    """
    def post(self, request, *args, **kwargs):
        data_list = request.data

        for data in data_list:
            create_model_entry(data)

        return Response({"success": True})

def create_model_entry(data):
    with transaction.atomic():
        # Use a database transaction to ensure that only one request at a time
        # can create the new entry.
        with LOCK:
            # Use a lock to ensure that only one thread at a time can execute
            # this block of code.
            existing_entries = Post.objects.filter(author=data["author_id"], title=data["title"])
            if existing_entries.exists():
                # An entry with the same field value already exists.
                return "Found Existing Entries"
            else:
                new_entry = Post.objects.create(**data)
                new_entry.save()
