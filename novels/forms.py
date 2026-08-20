from django import forms
from .models import Novel, Review

class NovelForm(forms.ModelForm):
    class Meta:
        model = Novel
        fields = ['title', 'synopsis', 'cover_image', 'genre', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full text-white bg-transparent rounded-lg px-4 py-3 focus:outline-none transition-colors',
                'style': 'border:1px solid rgba(124,58,237,.4); focus:border-color:#7C3AED;',
                'placeholder': 'Ej. Reencarné como un Slime de Nivel 99',
                'autocomplete': 'off',
            }),
            'synopsis': forms.Textarea(attrs={
                'class': 'w-full text-purple-200 bg-transparent rounded-lg px-4 py-3 focus:outline-none transition-colors resize-y',
                'style': 'border:1px solid rgba(124,58,237,.4); focus:border-color:#7C3AED; min-height:120px;',
                'placeholder': 'Escribe una sinopsis atrapante...',
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'w-full text-purple-300 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-brand file:text-white hover:file:bg-brand-dark cursor-pointer',
                'accept': 'image/*',
            }),
            'genre': forms.Select(attrs={
                'class': 'w-full text-white rounded-lg px-4 py-3 focus:outline-none transition-colors appearance-none',
                'style': 'background:rgba(13,11,30,.8); border:1px solid rgba(124,58,237,.4);',
            }),
            'rating': forms.Select(attrs={
                'class': 'w-full text-white rounded-lg px-4 py-3 focus:outline-none transition-colors appearance-none',
                'style': 'background:rgba(13,11,30,.8); border:1px solid rgba(124,58,237,.4);',
            }),
        }
        labels = {
            'title': 'Título de la Novela',
            'synopsis': 'Sinopsis',
            'cover_image': 'Portada (Opcional)',
            'genre': 'Género Principal',
            'rating': 'Clasificación de Edad',
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'body']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'w-full text-white rounded-lg px-4 py-3 focus:outline-none transition-colors appearance-none',
                'style': 'background:rgba(13,11,30,.8); border:1px solid rgba(124,58,237,.4);',
            }),
            'body': forms.Textarea(attrs={
                'class': 'w-full text-purple-200 bg-transparent rounded-lg px-4 py-3 focus:outline-none transition-colors resize-y',
                'style': 'border:1px solid rgba(124,58,237,.4); focus:border-color:#7C3AED; min-height:100px;',
                'placeholder': 'Escribe tu reseña aquí...',
            }),
        }
        labels = {
            'rating': 'Calificación',
            'body': 'Reseña',
        }
