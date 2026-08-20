from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Comment, CommentLike


@login_required
def toggle_like(request, comment_id):
    """Endpoint HTMX: da o quita el like de un comentario. Devuelve el botón actualizado."""
    if request.method != 'POST':
        return HttpResponse('')

    comment = get_object_or_404(Comment, pk=comment_id)
    like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)

    if not created:
        like.delete()
        is_liked = False
    else:
        is_liked = True

    return render(request, 'comments/partials/like_button.html', {
        'comment': comment,
        'is_liked': is_liked,
    })


@login_required
def delete_comment(request, comment_id):
    """Endpoint HTMX: elimina un comentario si el usuario es el autor."""
    comment = get_object_or_404(Comment, pk=comment_id)
    
    if request.method == 'DELETE' or request.method == 'POST':
        if comment.author == request.user:
            comment.delete()
            return HttpResponse('')  # Retorna vacío para eliminar del DOM con hx-swap="outerHTML"
            
    return HttpResponse(status=403)

