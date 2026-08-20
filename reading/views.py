from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse

from novels.models import Novel
from reading.models import Bookmark, AuthorFollow, AuthorSupport
from notifications.models import Notification

User = get_user_model()


@login_required
def library_view(request):
    """Biblioteca personal: novelas guardadas. Redirige al perfil que ya tiene la UI."""
    return redirect('/cuenta/perfil/?tab=biblioteca')


@login_required
def toggle_bookmark(request, novel_slug):
    """Endpoint HTMX: Añade o quita una novela de la biblioteca del usuario."""
    novel = get_object_or_404(Novel, slug=novel_slug, is_published=True)

    if request.method == 'POST':
        bookmark, created = Bookmark.objects.get_or_create(user=request.user, novel=novel)
        if not created:
            bookmark.delete()
            is_bookmarked = False
        else:
            is_bookmarked = True

        return render(request, 'reading/partials/bookmark_button.html', {
            'novel': novel,
            'is_bookmarked': is_bookmarked,
        })

    return HttpResponse('')


@login_required
def toggle_follow(request, username):
    """Endpoint HTMX: sigue o deja de seguir a un autor."""
    author = get_object_or_404(User, username=username)

    if author == request.user:
        return HttpResponse('')  # No te puedes seguir a ti mismo

    if request.method == 'POST':
        follow, created = AuthorFollow.objects.get_or_create(follower=request.user, author=author)
        if not created:
            follow.delete()
            is_following = False
        else:
            is_following = True

        followers_count = author.followers.count()
        return render(request, 'reading/partials/follow_button.html', {
            'author': author,
            'is_following': is_following,
            'followers_count': followers_count,
        })

    return HttpResponse('')


@login_required
def toggle_support(request, username):
    """Endpoint HTMX: apoya o retira el apoyo a un autor."""
    author = get_object_or_404(User, username=username)

    if author == request.user:
        return HttpResponse('')  # No te puedes apoyar a ti mismo

    if request.method == 'POST':
        support, created = AuthorSupport.objects.get_or_create(user=request.user, author=author)
        if not created:
            support.delete()
            is_supporting = False
        else:
            is_supporting = True
            # Notificar al autor
            Notification.objects.create(
                user=author,
                message=f'¡{request.user.username} apoyó tu trabajo! 💜',
                link=f'/cuenta/autor/{request.user.username}/',
            )

        supports_count = author.supports_received.count()
        return render(request, 'reading/partials/support_button.html', {
            'author': author,
            'is_supporting': is_supporting,
            'supports_count': supports_count,
            'user': request.user,  # el partial necesita 'user' para las condiciones
        })

    return HttpResponse('')
