from django.shortcuts import render, get_object_or_404, redirect
from .models import Board, Topic, Post
from .forms import NewTopicForm, PostForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.views.generic import UpdateView, ListView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse


def about(request):
    return render(request, 'about.html')


def home(request):
    boards = Board.objects.all()
    return render(request, 'home.html', {'boards': boards})


class BoardListView(ListView):
    model = Board
    context_object_name = 'boards'
    template_name = 'home.html'


def board_topics(request, pk):
    board = get_object_or_404(Board, pk=pk)
    queryset = board.topics.order_by(
        '-last_update').annotate(replies=Count('posts') - 1)
    page = request.GET.get('page', 1)
    paginator = Paginator(queryset, 20)
    try:
        topics = paginator.page(page)
    except PageNotAnInteger:
        # fallback to first page as default
        topics = paginator.page(1)
    except EmptyPage:
        # probably the user tried to add a larger page number in the url to
        # reach the last page, so we fallback to the last page
        topics = paginator.page(paginator.num_pages)
    return render(request, 'topics.html', {'board': board, 'topics': topics})


class TopicListView(ListView):
    model = Topic
    context_object_name = 'topics'
    template_name = 'topics.html'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        kwargs['board'] = self.board
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.board = get_object_or_404(Board, pk=self.kwargs.get('pk'))
        queryset = self.board.topics.order_by(
            '-last_update').annotate(replies=Count('posts') - 1)
        return queryset


@login_required
def new_topic(request, pk):
    board = get_object_or_404(Board, pk=pk)

    # if POST, this is form submission
    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.board = board
            topic.starter = request.user
            topic.save()
            post = Post.objects.create(
                message=form.cleaned_data.get('message'),
                topic=topic,
                created_by=request.user
            )
            # TODO: redirect to the created topic page listing current posts.
            # return redirect('board_topics', pk=board.pk)
            return redirect('topic_posts', pk=board.pk, topic_pk=topic.pk)
    else:
        form = NewTopicForm()

    # else render form
    return render(request, 'new_topic.html', {'board': board, 'form': form})


def topic_posts(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    topic.views += 1
    topic.save()
    return render(request, 'topic_posts.html', {'topic': topic})


class PostListView(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'topic_posts.html'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        # Ensure multiple views of a topic by the same user, count as 1 view.
        # On first view by logged in user, set session_key to True
        session_key = 'viewed_topic_{}'.format(self.topic.pk)
        if not self.request.session.get(session_key, False):
            self.topic.views += 1
            self.topic.save()
            self.request.session[session_key] = True

        kwargs['topic'] = self.topic
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.topic = get_object_or_404(Topic, board__pk=self.kwargs.get(
            'pk'), pk=self.kwargs.get('topic_pk'))
        queryset = self.topic.posts.order_by('created_at')
        return queryset


@login_required
def reply_topic(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.save()

            # set last_update field of the topic on reply save.
            topic.last_update = timezone.now()
            topic.save()

            topic_url = reverse('topic_posts', kwargs={
                'pk': pk, 'topic_pk': topic_pk})
            topic_post_url = '{url}?page={page}#post-{id}'.format(
                url=topic_url,
                id=post.pk,
                page=topic.get_page_count()
            )
            return redirect(topic_post_url)
    else:
        form = PostForm()
    return render(request, 'reply_topic.html', {'topic': topic, 'form': form})


@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView):
    model = Post
    fields = ('message', )
    template_name = 'edit_post.html'
    pk_url_kwarg = 'post_pk'
    context_object_name = 'post'

    def get_queryset(self):
        # ensure we filter the queryset to return only the post created by
        # currently logged in user! while this is OK, an unauthorized user is
        # going to get a 404-not-found rather than 403-unauthorized.
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.user)

    def form_valid(self, form):
        post = form.save(commit=False)
        post.updated_by = self.request.user
        post.updated_at = timezone.now()
        post.save()
        return redirect('topic_posts', pk=post.topic.board.pk, topic_pk=post.topic.pk)
