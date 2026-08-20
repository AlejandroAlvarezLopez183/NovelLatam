from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from reading.models import Bookmark, ReadingProgress

from .models import Novel, Review
from .forms import NovelForm, ReviewForm

def get_visible_novels(request, queryset):
    """Filtra las novelas excluyendo autores bloqueados o que han bloqueado al usuario."""
    if request.user.is_authenticated:
        from accounts.models import UserBlock
        blocked_by_me = UserBlock.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
        blocked_me = UserBlock.objects.filter(blocked=request.user).values_list('blocker_id', flat=True)
        return queryset.exclude(author_id__in=blocked_by_me).exclude(author_id__in=blocked_me)
    return queryset

def home(request):
    """Landing page principal — muestra hero, features, actualizaciones recientes y top novelas."""
    from django.db.models import Count
    from chapters.models import Chapter

    # Últimas novelas publicadas para la sección "Primeras Obras"
    featured_novels = get_visible_novels(
        request, Novel.objects.filter(is_published=True)
    ).order_by('-created_at')[:6]

    # Últimos capítulos publicados (para la sección de actualizaciones)
    recent_chapters_qs = (
        Chapter.objects
        .filter(is_published=True, novel__is_published=True)
        .select_related('novel', 'novel__author')
        .order_by('-created_at')
    )
    if request.user.is_authenticated:
        from accounts.models import UserBlock
        blocked_ids = (
            list(UserBlock.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)) +
            list(UserBlock.objects.filter(blocked=request.user).values_list('blocker_id', flat=True))
        )
        if blocked_ids:
            recent_chapters_qs = recent_chapters_qs.exclude(novel__author_id__in=blocked_ids)
    recent_chapters = recent_chapters_qs[:8]

    # Top 3 novelas por popularidad (bookmarks)
    top_novels = (
        get_visible_novels(request, Novel.objects.filter(is_published=True))
        .annotate(bookmarks_count=Count('bookmarked_by', distinct=True))
        .order_by('-bookmarks_count', '-created_at')[:3]
    )

    return render(request, 'novels/home.html', {
        'featured_novels': featured_novels,
        'recent_chapters':  recent_chapters,
        'top_novels':       top_novels,
    })


def novel_list(request):
    """Catálogo completo: explorar novelas publicadas con filtro por género, rating o búsqueda."""
    genero = request.GET.get('genero')
    rating_filter = request.GET.get('rating')
    query = request.GET.get('q')

    novels = get_visible_novels(request, Novel.objects.filter(is_published=True))

    if genero:
        novels = novels.filter(genre=genero)

    if rating_filter:
        novels = novels.filter(rating=rating_filter)

    if query:
        novels = novels.filter(
            Q(title__icontains=query) |
            Q(author__username__icontains=query) |
            Q(synopsis__icontains=query)
        )

    paginator = Paginator(novels, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # TOP Novelas (Tendencias) para mostrar en el encabezado
    from django.db.models import Count
    top_novels = (
        get_visible_novels(request, Novel.objects.filter(is_published=True))
        .annotate(bookmarks_count=Count('bookmarked_by', distinct=True))
        .order_by('-bookmarks_count', '-created_at')[:4]
    )

    return render(request, 'novels/list.html', {
        'novels': page_obj,
        'page_obj': page_obj,
        'genero_actual': genero,
        'rating_actual': rating_filter,
        'search_query': query,
        'top_novels': top_novels,
    })

def ranking_view(request):
    """Página de Leaderboard: clasifica las novelas por diferentes criterios y regiones."""
    sort_by = request.GET.get('sort', 'popular') # popular, rating
    region = request.GET.get('region', 'GLOBAL')
    
    # Obtenemos las opciones de países desde el modelo
    from accounts.models import COUNTRY_CHOICES
    
    # Filtramos las novelas publicadas y aplicamos el filtro de región si es necesario
    base_qs = Novel.objects.filter(is_published=True)
    if region != 'GLOBAL':
        base_qs = base_qs.filter(author__profile__country=region)

    novels = get_visible_novels(request, base_qs).annotate(
        bookmarks_count=Count('bookmarked_by', distinct=True),
        avg_rating=Avg('reviews__rating'),
        reviews_count=Count('reviews', distinct=True)
    )
    
    if sort_by == 'rating':
        novels = novels.order_by('-avg_rating', '-reviews_count', '-created_at')
        title = "Mejor Valoradas"
    else:
        # Por defecto: Popularidad (guardados en biblioteca)
        novels = novels.order_by('-bookmarks_count', '-avg_rating', '-created_at')
        title = "Más Populares"
        
    return render(request, 'novels/ranking.html', {
        'novels': novels[:100], # Top 100
        'sort_by': sort_by,
        'ranking_title': title,
        'current_region': region,
        'country_choices': COUNTRY_CHOICES,
    })



def quick_search(request):
    """Búsqueda rápida vía HTMX para autocompletado en el navbar."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return render(request, 'novels/partials/search_results.html', {'novels': []})
        
    novels = get_visible_novels(request, Novel.objects.filter(is_published=True)).filter(
        Q(title__icontains=query) | Q(author__username__icontains=query)
    )[:5]  # Limit to 5 results
    
    return render(request, 'novels/partials/search_results.html', {
        'novels': novels,
        'query': query,
    })

def novel_detail(request, slug):
    novel = get_object_or_404(
        get_visible_novels(request, Novel.objects.prefetch_related('chapters')),
        slug=slug,
    )
    # Si no es el autor, solo puede ver novelas publicadas
    if not novel.is_published and request.user != novel.author:
        from django.http import Http404
        raise Http404("Novela no publicada")

    if request.user == novel.author:
        chapters = novel.chapters.all().order_by('order')
    else:
        chapters = novel.chapters.filter(is_published=True).order_by('order')
    
    # Reviews y rating
    reviews = novel.reviews.select_related('user').all()
    if request.user.is_authenticated:
        from accounts.models import UserBlock
        blocked_ids = UserBlock.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
        if blocked_ids:
            reviews = reviews.exclude(user_id__in=blocked_ids)

    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
    user_review = None
    
    is_bookmarked = False
    read_chapter_ids = set()
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(user=request.user, novel=novel).exists()
        user_review = reviews.filter(user=request.user).first()
        read_chapter_ids = set(
            ReadingProgress.objects
            .filter(user=request.user, chapter__novel=novel)
            .values_list('chapter_id', flat=True)
        )
        
    # Formulario de reseñas
    if request.method == 'POST' and request.user.is_authenticated:
        if 'submit_review' in request.POST and not user_review:
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.novel = novel
                review.user = request.user
                review.save()
                return redirect('novels:detail', slug=novel.slug)
    
    review_form = ReviewForm() if not user_review else None
    
    # Calcular siguiente capítulo a leer
    next_chapter_to_read = None
    if is_bookmarked:
        bookmark = Bookmark.objects.filter(user=request.user, novel=novel).first()
        if bookmark and bookmark.last_read_chapter:
            # Buscar el siguiente al último leído
            next_chapter_to_read = chapters.filter(order__gt=bookmark.last_read_chapter.order).first()
            if not next_chapter_to_read:
                # Si no hay siguiente, sugerimos el último que leyó
                next_chapter_to_read = bookmark.last_read_chapter
        elif chapters.exists():
            next_chapter_to_read = chapters.first()
    elif chapters.exists():
        next_chapter_to_read = chapters.first()

    return render(request, 'novels/detail.html', {
        'novel': novel,
        'chapters': chapters,
        'chapters_count': chapters.count(),
        'is_bookmarked': is_bookmarked,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_form': review_form,
        'user_review': user_review,
        'next_chapter_to_read': next_chapter_to_read,
        'read_chapter_ids': read_chapter_ids,
    })


@login_required
def novel_create(request):
    if request.method == 'POST':
        form = NovelForm(request.POST, request.FILES)
        if form.is_valid():
            novel = form.save(commit=False)
            novel.author = request.user
            # Optional: automatically publish when created, or leave it as draft
            novel.is_published = True 
            novel.save()
            return redirect('novels:detail', slug=novel.slug)
    else:
        form = NovelForm()
    
    return render(request, 'novels/create.html', {'form': form})

@login_required
def novel_update(request, slug):
    novel = get_object_or_404(Novel, slug=slug, author=request.user)
    if request.method == 'POST':
        form = NovelForm(request.POST, request.FILES, instance=novel)
        if form.is_valid():
            form.save()
            return redirect('novels:detail', slug=novel.slug)
    else:
        form = NovelForm(instance=novel)
    
@login_required
def delete_review(request, review_id):
    """Endpoint HTMX para borrar una reseña si eres el autor."""
    review = get_object_or_404(Review, pk=review_id)
    if request.method == 'DELETE' or request.method == 'POST':
        if review.user == request.user:
            review.delete()
            return HttpResponse('')
    return HttpResponse(status=403)
