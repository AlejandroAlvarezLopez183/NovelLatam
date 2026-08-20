from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from chapters.models import Chapter
from comments.models import Comment
from novels.models import Novel
from reading.models import Bookmark, ReadingProgress, AuthorFollow
from notifications.models import Notification

# Etiquetas de advertencia disponibles para los capítulos
CONTENT_TAGS = [
    'Gore / Sangre',
    'Lenguaje Fuerte',
    'Tragedia',
    'Contenido Sexual (leve)',
    'Violencia extrema',
    'Temas sensibles',
]


def chapter_read(request, novel_slug, chapter_order):
    """Vista de lectura de un capítulo publicado."""
    from novels.views import get_visible_novels
    novel = get_object_or_404(
        get_visible_novels(request, Novel.objects.prefetch_related('chapters')),
        slug=novel_slug
    )
    
    # Si no es el autor y la novela no está publicada, 404
    if not novel.is_published and request.user != novel.author:
        from django.http import Http404
        raise Http404("Novela no publicada")

    if request.user == novel.author:
        chapter = get_object_or_404(novel.chapters, order=chapter_order)
    else:
        chapter = get_object_or_404(novel.chapters, order=chapter_order, is_published=True)

    # Verificar acceso a capítulos exclusivos para seguidores
    if chapter.followers_only:
        is_following = False
        if request.user.is_authenticated:
            is_following = AuthorFollow.objects.filter(
                follower=request.user, author=novel.author
            ).exists()
        # El autor propio siempre tiene acceso
        if not is_following and request.user != novel.author:
            return render(request, 'chapters/locked.html', {
                'novel': novel,
                'chapter': chapter,
                'is_following': is_following,
            })

    # Capítulos anterior y siguiente
    if request.user == novel.author:
        prev_chapter = Chapter.objects.filter(novel=novel, order__lt=chapter_order).order_by('-order').first()
        next_chapter = Chapter.objects.filter(novel=novel, order__gt=chapter_order).order_by('order').first()
    else:
        prev_chapter = Chapter.objects.filter(novel=novel, order__lt=chapter_order, is_published=True).order_by('-order').first()
        next_chapter = Chapter.objects.filter(novel=novel, order__gt=chapter_order, is_published=True).order_by('order').first()

    # Solo comentarios generales (sin parent y sin paragraph_index)
    general_comments = chapter.comments.filter(is_hidden=False, parent=None, paragraph_index__isnull=True).select_related('author').prefetch_related('replies__author', 'likes')

    # Procesar contenido en párrafos y contar comentarios por párrafo
    content = chapter.content.strip()
    if '<p' in content or '<div' in content:
        # El contenido es HTML (probablemente de un editor WYSIWYG)
        import re
        # Dividir por etiquetas de cierre de bloque comunes
        parts = re.split(r'(</p>|</div>|<br\s*/?>\s*<br\s*/?>)', content)
        raw_paragraphs = []
        current = ""
        for part in parts:
            if part in ['</p>', '</div>'] or part.startswith('<br'):
                if current.strip():
                    raw_paragraphs.append(current.strip() + part)
                current = ""
            else:
                current += part
        if current.strip():
            raw_paragraphs.append(current.strip())
    else:
        # Texto plano
        raw_paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
    
    from django.db.models import Count
    paragraph_comment_counts = dict(
        chapter.comments.filter(is_hidden=False, paragraph_index__isnull=False, parent=None)
        .values('paragraph_index')
        .annotate(c=Count('id'))
        .values_list('paragraph_index', 'c')
    )
    
    paragraphs = []
    for i, text in enumerate(raw_paragraphs):
        paragraphs.append({
            'index': i,
            'text': text,
            'comments_count': paragraph_comment_counts.get(i, 0)
        })

    # Actualizar progreso de lectura y filtrar bloqueados
    blocked_ids = []
    if request.user.is_authenticated:
        from accounts.models import UserBlock
        blocked_ids = UserBlock.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
        if blocked_ids:
            general_comments = general_comments.exclude(author_id__in=blocked_ids)

        bookmark = Bookmark.objects.filter(user=request.user, novel=novel).first()
        if bookmark and (not bookmark.last_read_chapter or bookmark.last_read_chapter.order < chapter.order):
            bookmark.last_read_chapter = chapter
            bookmark.save()
        ReadingProgress.objects.get_or_create(user=request.user, chapter=chapter)

    return render(request, 'chapters/read.html', {
        'novel':        novel,
        'chapter':      chapter,
        'paragraphs':   paragraphs,
        'prev_chapter': prev_chapter,
        'next_chapter': next_chapter,
        'comments':     general_comments,
        'comments_count': chapter.comments.filter(is_hidden=False, paragraph_index__isnull=True).count(),
        'blocked_ids':  blocked_ids,
    })


@login_required
def comment_create(request, chapter_id):
    """Endpoint HTMX: crea un comentario o respuesta y devuelve el HTML del nuevo item."""
    chapter = get_object_or_404(Chapter, pk=chapter_id, is_published=True)
    body = request.POST.get('body', '').strip()
    parent_id = request.POST.get('parent_id')
    paragraph_index = request.POST.get('paragraph_index')

    if request.method == 'POST' and body:
        parent = None
        if parent_id:
            parent = Comment.objects.filter(pk=parent_id, chapter=chapter, parent=None).first()

        p_index = None
        if paragraph_index and paragraph_index.isdigit():
            p_index = int(paragraph_index)

        comment = Comment.objects.create(
            chapter=chapter,
            author=request.user,
            body=body,
            parent=parent,
            paragraph_index=p_index,
        )

        if parent:
            # Devolver solo el item de respuesta para insertarlo en el sub-hilo
            return render(request, 'chapters/partials/reply_item.html', {'reply': comment, 'chapter': chapter})

        return render(request, 'chapters/partials/comment_item.html', {'comment': comment, 'chapter': chapter})

    return HttpResponse('')

def paragraph_comments(request, chapter_id, paragraph_index):
    """Endpoint HTMX: Carga los comentarios de un párrafo específico para mostrarlos en el off-canvas."""
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    
    comments = chapter.comments.filter(
        is_hidden=False, 
        parent=None, 
        paragraph_index=paragraph_index
    ).select_related('author').prefetch_related('replies__author', 'likes')
    
    blocked_ids = []
    if request.user.is_authenticated:
        from accounts.models import UserBlock
        blocked_ids = UserBlock.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
        if blocked_ids:
            comments = comments.exclude(author_id__in=blocked_ids)
            
    # Extraer el texto del párrafo para mostrarlo como contexto
    content = chapter.content.strip()
    if '<p' in content or '<div' in content:
        import re
        parts = re.split(r'(</p>|</div>|<br\s*/?>\s*<br\s*/?>)', content)
        raw_paragraphs = []
        current = ""
        for part in parts:
            if part in ['</p>', '</div>'] or part.startswith('<br'):
                if current.strip():
                    raw_paragraphs.append(current.strip() + part)
                current = ""
            else:
                current += part
        if current.strip():
            raw_paragraphs.append(current.strip())
    else:
        raw_paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        
    paragraph_text = raw_paragraphs[paragraph_index] if paragraph_index < len(raw_paragraphs) else ''
            
    return render(request, 'chapters/partials/paragraph_comments_list.html', {
        'chapter': chapter,
        'paragraph_index': paragraph_index,
        'paragraph_text': paragraph_text,
        'comments': comments,
        'blocked_ids': blocked_ids,
    })


@login_required
def chapter_create(request, novel_slug):
    """Editor de capítulo: crea un nuevo capítulo para una novela del autor."""
    novel = get_object_or_404(Novel, slug=novel_slug, author=request.user)

    # Siguiente número de capítulo auto-calculado
    last_order = (
        Chapter.objects.filter(novel=novel).order_by('-order').values_list('order', flat=True).first()
    )
    next_order = (last_order or 0) + 1

    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        content     = request.POST.get('content', '').strip()
        publish_now = request.POST.get('action') == 'publish'
        publish_at_raw = request.POST.get('publish_at', '').strip()
        author_note = request.POST.get('author_note', '').strip()
        selected_tags = request.POST.getlist('tags')  # lista de strings
        followers_only = request.POST.get('followers_only') == 'on'

        if not title or not content:
            messages.error(request, 'El título y el contenido son obligatorios.')
        else:
            # Hora de publicación
            publish_at = None
            if publish_at_raw:
                publish_at = parse_datetime(publish_at_raw)

            # Añadir notas del autor al final del contenido si existen
            full_content = content
            if author_note:
                full_content += f'\n\n[Nota del autor: {author_note}]'

            chapter = Chapter.objects.create(
                novel=novel,
                title=title,
                content=full_content,
                order=next_order,
                is_published=publish_now,
                publish_at=publish_at if not publish_now else None,
                followers_only=followers_only,
            )

            if publish_now:
                link = f"/novela/{novel.slug}/capitulo/{chapter.order}/"
                message_text = f"¡Nuevo capítulo disponible! {novel.title} — Cap. {chapter.order}: {title}"
                notifications_to_create = []
                already_notified = set()

                # Notificar a lectores que tienen la novela en su biblioteca
                bookmarks = Bookmark.objects.filter(novel=novel).select_related('user')
                for b in bookmarks:
                    if b.user != request.user and b.user_id not in already_notified:
                        notifications_to_create.append(
                            Notification(user=b.user, message=message_text, link=link)
                        )
                        already_notified.add(b.user_id)

                # Notificar también a los seguidores del autor
                follows = AuthorFollow.objects.filter(author=request.user).select_related('follower')
                for f in follows:
                    if f.follower != request.user and f.follower_id not in already_notified:
                        notifications_to_create.append(
                            Notification(user=f.follower, message=message_text, link=link)
                        )
                        already_notified.add(f.follower_id)

                if notifications_to_create:
                    Notification.objects.bulk_create(notifications_to_create)

                messages.success(request, f'Capítulo {next_order} publicado correctamente.')
                return redirect('novels:detail', slug=novel.slug)
            else:
                messages.success(request, f'Borrador del capítulo {next_order} guardado.')
                return redirect('chapters:create', novel_slug=novel.slug)

    return render(request, 'chapters/create.html', {
        'novel':       novel,
        'next_order':  next_order,
        'content_tags': CONTENT_TAGS,
    })

@login_required
def chapter_update(request, novel_slug, chapter_order):
    """Editor de capítulo: modifica un capítulo ya existente."""
    novel = get_object_or_404(Novel, slug=novel_slug, author=request.user)
    chapter = get_object_or_404(Chapter, novel=novel, order=chapter_order)

    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        content     = request.POST.get('content', '').strip()
        
        if not title or not content:
            messages.error(request, 'El título y el contenido son obligatorios.')
        else:
            chapter.title = title
            chapter.content = content
            chapter.followers_only = request.POST.get('followers_only') == 'on'
            
            action = request.POST.get('action')
            if action == 'publish' and not chapter.is_published:
                chapter.is_published = True
                
                # Enviar notificaciones de publicación si se publica por primera vez
                link = f"/novela/{novel.slug}/capitulo/{chapter.order}/"
                message_text = f"¡Nuevo capítulo disponible! {novel.title} — Cap. {chapter.order}: {title}"
                notifications_to_create = []
                already_notified = set()

                # Notificar a lectores que tienen la novela en su biblioteca
                bookmarks = Bookmark.objects.filter(novel=novel).select_related('user')
                for b in bookmarks:
                    if b.user != request.user and b.user_id not in already_notified:
                        notifications_to_create.append(
                            Notification(user=b.user, message=message_text, link=link)
                        )
                        already_notified.add(b.user_id)

                # Notificar también a los seguidores del autor
                follows = AuthorFollow.objects.filter(author=request.user).select_related('follower')
                for f in follows:
                    if f.follower != request.user and f.follower_id not in already_notified:
                        notifications_to_create.append(
                            Notification(user=f.follower, message=message_text, link=link)
                        )
                        already_notified.add(f.follower_id)

                if notifications_to_create:
                    Notification.objects.bulk_create(notifications_to_create)
                
            chapter.save()
            
            if chapter.is_published:
                messages.success(request, f'Capítulo {chapter.order} actualizado y publicado correctamente.')
            else:
                messages.success(request, f'Borrador del capítulo {chapter.order} actualizado correctamente.')
                
            return redirect('chapters:read', novel_slug=novel.slug, chapter_order=chapter.order)

    return render(request, 'chapters/update.html', {
        'novel':       novel,
        'chapter':     chapter,
        'content_tags': CONTENT_TAGS,
    })
