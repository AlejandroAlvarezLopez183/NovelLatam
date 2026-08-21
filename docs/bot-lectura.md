# 🎙️ Bot de Lectura — Novelatam

## Estado actual: ✅ Fase 1 Implementada

**Fecha de implementación:** Agosto 2026  
**Archivo clave:** `chapters/templates/chapters/read.html`

---

## Descripción

El bot de lectura permite a los usuarios escuchar el contenido de cualquier capítulo en voz alta directamente desde el lector, sin necesidad de instalar ninguna aplicación adicional.

El botón **"Escuchar"** aparece en la barra superior del lector, junto al botón de Ajustes. Al pulsarlo, el texto del capítulo comienza a leerse automáticamente. Pulsarlo de nuevo lo detiene.

---

## Fase 1 — Web Speech API (Activa)

### Tecnología

Utiliza la **Web Speech API** nativa del navegador (`SpeechSynthesisUtterance`). Es una API estándar, gratuita e ilimitada que viene incorporada en todos los navegadores modernos.

```
Navegador del usuario
        ↓
JavaScript llama a window.speechSynthesis.speak()
        ↓
El sistema operativo del usuario sintetiza la voz
        ↓
Audio reproducido localmente (sin usar el servidor)
```

### Ventajas
- ✅ **Costo: $0.00** — No consume recursos del servidor
- ✅ **Sin límites** de requests ni caracteres
- ✅ Funciona offline
- ✅ Latencia cero (instantáneo)

### Compatibilidad de voces por plataforma

| Plataforma | Motor de voz | Calidad |
|---|---|---|
| iPhone / Safari | Voz de Siri (Apple) | ⭐⭐⭐⭐⭐ Excelente |
| Android / Chrome | Google TTS | ⭐⭐⭐⭐ Muy buena |
| Windows / Edge | Microsoft Azure Neural | ⭐⭐⭐⭐ Muy buena |
| Windows / Chrome | Google TTS | ⭐⭐⭐⭐ Muy buena |
| macOS | Voz del sistema (Alex, etc.) | ⭐⭐⭐⭐ Muy buena |
| Linux / Brave | espeak-ng / MBROLA | ⭐⭐ Básica (problema de desarrollo local) |

> **Nota para desarrollo local en Linux:** El navegador necesita el paquete `speech-dispatcher` instalado y Brave debe lanzarse con la bandera `--enable-speech-dispatcher`. Esto es un problema exclusivo del entorno de desarrollo, no afecta a usuarios en producción.

### Detalles de implementación

**Extracción de texto:**  
El script selecciona todos los elementos `<p>` dentro del `#novel-content-area`, extrae su `textContent` y los une con `. ` para que el sintetizador haga pausas naturales entre párrafos.

**Selección de voz:**  
El código busca automáticamente una voz cuyo idioma empiece por `es` (español) usando `speechSynthesis.getVoices()`. Si no encuentra ninguna voz en español disponible, establece `lang = 'es'` como fallback.

**Manejo de errores:**  
Si el navegador no puede sintetizar el audio (por ejemplo, en Linux sin configurar), se muestra un toast notification no bloqueante en la parte inferior de la pantalla con el mensaje `"🔇 Voz no disponible"`. El toast desaparece automáticamente en 3 segundos y no interrumpe la experiencia del usuario.

**Limpieza al navegar:**  
El evento `beforeunload` cancela cualquier síntesis activa para que el audio no continúe reproduciéndose si el usuario navega a otro capítulo.

---

## Fase 2 — Piper TTS + Celery + Cloudflare R2 (Pendiente)

### ¿Cuándo implementar?

Cuando la plataforma tenga autores activos publicando capítulos de forma regular y exista demanda real de la función de audio. No construir antes de que haya usuarios reales que lo pidan.

### ¿Qué es Piper TTS?

[Piper](https://github.com/rhasspy/piper) es un motor de síntesis de voz neuronal de código abierto desarrollado por la comunidad de Home Assistant. Genera audio de calidad casi humana completamente offline, sin APIs de pago.

**Prueba realizada (Agosto 2026):**
- Modelo utilizado: `es_MX-claude-high.onnx`
- Texto de 7 palabras → audio de 5 segundos
- Tiempo de generación: 3.12 segundos de CPU
- Calidad: ⭐⭐⭐⭐⭐ — Notablemente mejor que la Web Speech API en Linux

### Arquitectura propuesta

```
Autor publica / actualiza un capítulo
        ↓
Django signal: post_save en el modelo Chapter
        ↓
Se encola una tarea en Celery (no bloquea la web)
        ↓
Worker de Celery ejecuta Piper TTS con el texto del capítulo
        ↓
Se genera un archivo .mp3 (comprimido con ffmpeg)
        ↓
El archivo se sube a Cloudflare R2 y se guarda la URL en el modelo
        ↓
El botón "Escuchar" en el lector carga el <audio src="url_de_r2">
        ↓ 
El usuario escucha el audio directamente desde R2 (CDN global)
```

### Estimación de recursos

| Métrica | Valor aproximado |
|---|---|
| RAM por generación | ~350 MB |
| Tiempo CPU (capítulo normal 2k palabras) | ~60-90 segundos |
| Tamaño audio .mp3 final | ~5-8 MB por capítulo |
| Almacenamiento R2 gratis | 10 GB / mes (~1,200 capítulos) |
| Costo por capítulo en R2 | $0.00 (dentro del tier gratuito) |

### Cambios técnicos requeridos

#### Backend Django

1. **Campo en el modelo `Chapter`:**
   ```python
   # chapters/models.py
   audio_url = models.URLField(blank=True, null=True, help_text="URL del audio generado por Piper TTS en R2")
   audio_generated_at = models.DateTimeField(null=True, blank=True)
   ```

2. **Tarea de Celery:**
   ```python
   # chapters/tasks.py
   @shared_task
   def generate_chapter_audio(chapter_id):
       chapter = Chapter.objects.get(id=chapter_id)
       texto = chapter.content  # texto plano del capítulo
       # 1. Llamar a Piper → generar .wav
       # 2. Convertir a .mp3 con ffmpeg
       # 3. Subir a Cloudflare R2
       # 4. Guardar URL en chapter.audio_url
   ```

3. **Signal para disparo automático:**
   ```python
   # chapters/signals.py
   @receiver(post_save, sender=Chapter)
   def trigger_audio_generation(sender, instance, **kwargs):
       if instance.is_published and not instance.audio_url:
           generate_chapter_audio.delay(instance.id)
   ```

#### Frontend

Reemplazar la lógica de Web Speech API por un reproductor `<audio>` HTML5 si `chapter.audio_url` está disponible. Si no hay audio pre-generado, caer de vuelta a la Web Speech API como respaldo.

```html
{% if chapter.audio_url %}
  <!-- Piper audio disponible -->
  <audio id="piper-audio" src="{{ chapter.audio_url }}" preload="none"></audio>
{% else %}
  <!-- Fallback: Web Speech API -->
{% endif %}
```

### Dependencias del servidor

```
piper (binario)                → Motor TTS neuronal
piper-voice-es_MX-claude-high  → Modelo de voz en español
ffmpeg                         → Conversión WAV → MP3
celery + redis                 → Cola de tareas asíncronas
boto3 / cloudflare-python      → Upload a R2
```

---

## Resumen de decisiones tomadas

| Decisión | Razón |
|---|---|
| Web Speech API para Fase 1 | Costo $0, sin servidor, funciona en todos los dispositivos de usuarios reales |
| Piper TTS descartado para Fase 1 | Requiere Celery + R2 + más infraestructura, no justificado sin base de usuarios |
| Piper TTS elegido para Fase 2 | La mejor opción gratis/offline, calidad excelente, sin lock-in de APIs de pago |
| ElevenLabs descartado | Costo por carácter, no viable para plataforma de lectura con capítulos largos |
| Google Cloud TTS descartado | Costo por carácter, mismo problema que ElevenLabs |
