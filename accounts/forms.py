from django import forms
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    """Formulario para editar la bio, avatar y website del perfil."""

    class Meta:
        model = UserProfile
        fields = ['avatar', 'cover_photo', 'bio', 'website', 'country']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'w-full text-purple-200 bg-transparent rounded-lg px-4 py-3 '
                         'focus:outline-none transition-colors resize-none',
                'style': 'border:1px solid rgba(124,58,237,.4); min-height:100px;',
                'placeholder': 'Cuéntale algo a la comunidad sobre ti...',
                'maxlength': '500',
                'rows': '4',
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
                'id': 'avatar-input',
            }),
            'cover_photo': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
                'id': 'cover-input',
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full text-white bg-transparent rounded-lg px-4 py-3 '
                         'focus:outline-none transition-colors',
                'style': 'border:1px solid rgba(124,58,237,.4);',
                'placeholder': 'https://tu-blog-o-redes-sociales.com',
            }),
            'country': forms.Select(attrs={
                'class': 'w-full text-purple-200 bg-[#0D0B1E] rounded-lg px-4 py-3 '
                         'focus:outline-none transition-colors border-brand/40',
                'style': 'border:1px solid rgba(124,58,237,.4);',
            }),
        }
        labels = {
            'avatar': 'Foto de perfil',
            'cover_photo': 'Foto de portada',
            'bio': 'Biografía',
            'website': 'Sitio web / Redes sociales',
            'country': 'País de Residencia',
        }
