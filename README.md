# Plataforma de Novelas Web

Plataforma enfocada en isekai, fantasía juvenil, aventuras y novelas ligeras.
Stack: Django + Tailwind CSS + HTMX. Ver `docs/arquitectura.md` para el
documento completo de arquitectura y roadmap.

## Estructura del proyecto

```
config/          # settings, urls raíz, wsgi/asgi (el "proyecto" de Django)
accounts/        # registro, login, perfiles
novels/          # modelo Novel, explorar, detalle, crear
chapters/        # modelo Chapter (capítulos de cada novela)
reading/         # biblioteca personal, seguir autores
comments/        # comentarios por capítulo
moderation/      # reportes y herramientas de moderación
core/            # utilidades compartidas entre apps
templates/       # templates globales (base.html, navbar, footer)
static/          # CSS/JS propios (además del CDN de Tailwind/HTMX)
docs/            # documentación técnica del proyecto
```

## Cómo arrancar en local

```bash
# 1. Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate        # en Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Copiar variables de entorno
cp .env.example .env

# 4. Crear las tablas de la base de datos
python manage.py migrate

# 5. Crear tu usuario administrador
python manage.py createsuperuser

# 6. Levantar el servidor de desarrollo
python manage.py runserver
```

Abre `http://127.0.0.1:8000/` para el sitio y `http://127.0.0.1:8000/admin/`
para el panel de administración (login con el superusuario del paso 5).

## Próximos pasos de desarrollo

Ver la sección 7 de `docs/arquitectura.md` — resumen rápido:

1. Completar el formulario real de creación de novela (`novels/views.py::novel_create`)
2. Construir las vistas de capítulos (`chapters/` — actualmente solo tiene el modelo)
3. Conectar `reading/` con un modelo real de biblioteca/seguir autores
4. Agregar sistema de comentarios en la vista de capítulo usando HTMX
   (crear comentario sin recargar la página)
5. Antes de producción: migrar Tailwind del CDN a una build local
   (`npm install -D tailwindcss` + configurar purge de clases no usadas)

## Notas de seguridad ya cubiertas por Django (no las desactives)

- CSRF: activo por defecto en todos los formularios (`{% csrf_token %}`)
- SQL injection: prevenido automáticamente al usar el ORM (evita `.raw()` con
  datos de usuario sin sanitizar)
- XSS: los templates escapan variables por defecto (evita `|safe` con
  contenido escrito por usuarios, como sinopsis o comentarios)
- Contraseñas: Django las guarda con hash seguro (PBKDF2) automáticamente
