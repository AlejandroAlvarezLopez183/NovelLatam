from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render

from novels.models import Novel
from reading.models import Bookmark, ReadingProgress, AuthorFollow, AuthorSupport
from .forms import UserProfileForm
from .models import UserBlock, UserProfile

User = get_user_model()


def register_view(request):
    """Registro de nuevo usuario (autor/lector son la misma cuenta)."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cuenta creada. ¡Bienvenido!')
            return redirect('novels:list')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('novels:list')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Sesión cerrada.')
    return redirect('novels:list')


@login_required
def profile_view(request):
    """Perfil del usuario: estadísticas, biblioteca y novelas publicadas."""
    user = request.user

    # Novelas publicadas por el autor
    published_novels = Novel.objects.filter(
        author=user, is_published=True
    ).prefetch_related('chapters')

    # Novelas guardadas en la biblioteca
    bookmarks = Bookmark.objects.filter(user=user).select_related('novel', 'last_read_chapter')
    bookmarked_novels = [b.novel for b in bookmarks]

    # Estadísticas reales desde ReadingProgress
    reading_qs = ReadingProgress.objects.filter(user=user).select_related('chapter')
    chapters_read = reading_qs.count()
    total_words = sum(len(rp.chapter.content.split()) for rp in reading_qs)
    reading_hours = round(total_words / 15000, 1)  # ~250 palabras/min => 15000/hr

    novels_read = bookmarks.count()
    comments_count = user.comments.count() if hasattr(user, 'comments') else 0

    # Seguidores y seguidos
    followers_count = user.followers.count()
    following_count = user.following.count()

    # Medallas de honor
    badges = _compute_badges(user, published_novels, chapters_read)

    # Perfil extendido (bio, avatar, website)
    user_profile, _ = UserProfile.objects.get_or_create(user=user)

    from .models import ProfileWallPost
    wall_posts = ProfileWallPost.objects.filter(author=user)

    return render(request, 'accounts/profile.html', {
        'profile_user':    user,
        'published_novels': published_novels,
        'bookmarked_novels': bookmarked_novels,
        'novels_count':    novels_read,
        'chapters_count':  chapters_read,
        'reading_hours':   reading_hours,
        'comments_count':  comments_count,
        'followers_count': followers_count,
        'following_count': following_count,
        'badges':          badges,
        'tab':             request.GET.get('tab', 'biblioteca'),
        'user_profile':    user_profile,
        'wall_posts':      wall_posts,
    })


def _compute_badges(user, published_novels, chapters_read):
    """Devuelve la lista de medallas desbloqueadas por el usuario."""
    badges = []

    # Medalla: Lector Voraz
    badges.append({
        'icon': '🔥',
        'name': 'Lector Voraz',
        'desc': 'Lee 100 capítulos en una semana',
        'unlocked': chapters_read >= 100,
        'color': '#F59E0B',
    })

    # Medalla: Primer Capítulo
    has_published = published_novels.exists()
    badges.append({
        'icon': '✏️',
        'name': 'Primer Capítulo',
        'desc': 'Escribe y publica tu primera obra',
        'unlocked': has_published,
        'color': '#7C3AED',
    })

    # Medalla: Autor Fundador (cuenta creada en los primeros días del sitio)
    badges.append({
        'icon': '🏅',
        'name': 'Autor Fundador',
        'desc': 'Únete durante el prelanzamiento',
        'unlocked': True,   # Todos los primeros usuarios la tienen
        'color': '#D97706',
    })

    return badges

from django.shortcuts import get_object_or_404


@login_required
def edit_profile_view(request):
    """Vista para editar bio, avatar y website del perfil propio."""
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Perfil actualizado correctamente!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, 'accounts/edit_profile.html', {'form': form})


def author_profile_view(request, username):
    """Perfil público de un autor para ver sus novelas publicadas."""
    User = get_user_model()
    author = get_object_or_404(User, username=username)

    # Verificar bloqueos (si A bloquea a B, o B bloquea a A, no se pueden ver los perfiles)
    is_blocked = False
    if request.user.is_authenticated and request.user != author:
        if UserBlock.objects.filter(blocker=author, blocked=request.user).exists():
            messages.error(request, "No puedes acceder al perfil de este usuario.")
            return redirect('novels:list')
            
        is_blocked = UserBlock.objects.filter(blocker=request.user, blocked=author).exists()

    published_novels = Novel.objects.filter(author=author, is_published=True).order_by('-created_at')

    # Datos de seguimiento
    followers_count = author.followers.count()
    is_following = False
    is_supporting = False
    supports_count = author.supports_received.count()
    author_profile = getattr(author, 'profile', None)

    if request.user.is_authenticated and request.user != author:
        is_following = AuthorFollow.objects.filter(follower=request.user, author=author).exists()
        is_supporting = AuthorSupport.objects.filter(user=request.user, author=author).exists()

    from .models import ProfileWallPost
    wall_posts = ProfileWallPost.objects.filter(author=author)

    return render(request, 'accounts/author_profile.html', {
        'author': author,
        'published_novels': published_novels,
        'followers_count': followers_count,
        'is_following': is_following,
        'is_blocked': is_blocked,
        'is_supporting': is_supporting,
        'supports_count': supports_count,
        'author_profile': author_profile,
        'wall_posts': wall_posts,
        'tab': request.GET.get('tab', 'publicadas'),
    })


@login_required
def toggle_block(request, username):
    """Endpoint HTMX: bloquea o desbloquea a un usuario."""
    blocked_user = get_object_or_404(User, username=username)

    if blocked_user == request.user:
        return HttpResponse('')  # No te puedes bloquear a ti mismo

    if request.method == 'POST':
        block, created = UserBlock.objects.get_or_create(blocker=request.user, blocked=blocked_user)
        if not created:
            block.delete()
            is_blocked = False
        else:
            is_blocked = True
            # Si lo bloquea, dejamos de seguirlo automáticamente
            AuthorFollow.objects.filter(follower=request.user, author=blocked_user).delete()

        # Si la petición viene de la página de bloqueados, el target será #block-card-...
        target = request.headers.get('HX-Target', '')
        if target.startswith('block-card-'):
            # Devolvemos un span vacío y oculto para asegurar que la tarjeta desaparezca
            return HttpResponse(f'<span id="{target}" style="display:none;"></span>')

        return render(request, 'accounts/partials/block_button.html', {
            'author': blocked_user,
            'is_blocked': is_blocked,
        })

    return HttpResponse('')


@login_required
def blocked_users_view(request):
    """Muestra la lista de usuarios bloqueados por el usuario actual."""
    blocks = UserBlock.objects.filter(blocker=request.user).select_related('blocked')
    return render(request, 'accounts/blocked_users.html', {'blocks': blocks})


@login_required
def author_dashboard_view(request):
    """Panel de autor para ver métricas y analíticas de sus obras."""
    from django.db.models import Count, Sum
    from reading.models import ReadingProgress

    user = request.user
    
    # Métricas Globales
    followers_count = user.followers.count()
    supports_count = user.supports_received.count()
    
    # Todas las novelas del usuario
    novels_qs = user.novels.prefetch_related('chapters')
    
    total_views = ReadingProgress.objects.filter(chapter__novel__author=user).count()
    total_bookmarks = sum(novel.bookmarked_by.count() for novel in novels_qs)
    
    # Procesar novelas para la UI
    novel_data = []
    for novel in novels_qs.order_by('-created_at'):
        chapters = novel.chapters.all()
        # Vistas de esta novela
        novel_views = ReadingProgress.objects.filter(chapter__novel=novel).count()
        novel_bookmarks = novel.bookmarked_by.count()
        
        # Desglose por capítulo
        chapter_data = []
        for chapter in chapters:
            chapter_views = chapter.readers.count()
            chapter_data.append({
                'chapter': chapter,
                'views': chapter_views,
            })
            
        novel_data.append({
            'novel': novel,
            'total_views': novel_views,
            'total_bookmarks': novel_bookmarks,
            'chapter_count': chapters.count(),
            'chapters': chapter_data,
        })
        
    return render(request, 'accounts/author_dashboard.html', {
        'followers_count': followers_count,
        'supports_count': supports_count,
        'total_views': total_views,
        'total_bookmarks': total_bookmarks,
        'novel_data': novel_data,
    })


@login_required
def post_to_wall(request):
    """Permite al autor publicar en su propio muro. Responde con HTMX."""
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            from .models import ProfileWallPost
            # Solo el autor puede publicar en su propio muro
            post = ProfileWallPost.objects.create(author=request.user, content=content)
            
            # Devolvemos el post recién creado (idealmente dentro de un template parcial o directamente el HTML)
            # Para mantenerlo simple y bonito, lo renderizamos inline
            import django.template
            template = django.template.Template('''
                <div class="glass p-4 rounded-xl mb-4 border border-brand/20 reveal active fade-up visible">
                    <div class="flex justify-between items-start mb-2">
                        <div class="flex items-center gap-2">
                            {% if post.author.profile.avatar %}
                                <img src="{{ post.author.profile.avatar.url }}" class="w-8 h-8 rounded-full object-cover border border-brand/50">
                            {% else %}
                                <div class="w-8 h-8 rounded-full bg-brand/30 flex items-center justify-center text-xs font-bold text-white">{{ post.author.username.0|upper }}</div>
                            {% endif %}
                            <span class="font-bold text-white">{{ post.author.username }}</span>
                            <span class="bg-brand/20 text-brand-light text-[10px] font-black uppercase px-2 py-0.5 rounded">Autor</span>
                        </div>
                        <span class="text-xs text-purple-400">Ahora mismo</span>
                    </div>
                    <p class="text-purple-200 text-sm whitespace-pre-wrap">{{ post.content }}</p>
                </div>
            ''')
            context = django.template.Context({'post': post})
            return HttpResponse(template.render(context))
    return HttpResponse('Error', status=400)
