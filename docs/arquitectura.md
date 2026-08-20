# Plataforma de Novelas Web — Documento de Arquitectura y Alcance

> Proyecto personal, desarrollo en ratos libres, un solo desarrollador (por ahora).
> Principio rector: **no construir para el éxito que todavía no tienes.**

---

## 1. Alcance (Scope)

### 1.1 Filosofía de alcance para un solo dev con tiempo limitado

La regla más importante en este documento: **cada feature que agregas es mantenimiento futuro que tú solo vas a cargar.** Antes de construir algo, pregúntate: ¿esto es indispensable para que un autor publique y un lector lea, o es un "nice to have" que puede esperar a la v2?

### 1.2 MVP real (lo mínimo para lanzar con tu grupo de WhatsApp)

**Debe tener:**
- Registro/login de usuarios (autor y lector son el mismo tipo de cuenta, con perfil de autor opcional)
- Crear/editar/publicar novela (título, sinopsis, portada, género, rating)
- Subir capítulos (editor de texto simple, orden, programar publicación)
- Lista de novelas con filtro por género/subgénero
- Página de novela con lista de capítulos
- Lector de capítulo (texto simple, cómodo, modo oscuro)
- Sistema de seguir autor / biblioteca personal ("guardado para leer")
- Comentarios básicos por capítulo
- Panel de administración mínimo (tú necesitas poder moderar sin escribir SQL a mano)

**NO debe tener en el MVP** (aunque las hayamos platicado, van después):
- Feed tipo swipe de descubrimiento
- Sistema de monedas / moneda social
- Publicidad integrada
- Glosario/wiki auto-generado
- Rankings por subgénero
- Eventos en vivo / chat

Esto no es descartarlas — es secuenciarlas. Lanzas con lo mínimo, validas que la gente publique y lea, y luego construyes sobre una base que ya sabes que funciona.

### 1.3 Fases del roadmap

| Fase | Objetivo | Qué se agrega |
|---|---|---|
| **Fase 0 — Validación** | Confirmar que autores publican y lectores leen | MVP de la sección 1.2, con tu grupo de WhatsApp como usuarios fundadores |
| **Fase 1 — Retención** | Que la gente vuelva | Notificaciones de nuevo capítulo, sistema de seguir, mejoras de lector (ajustar tipografía/tamaño), comentarios con likes |
| **Fase 2 — Descubrimiento** | Crecer más allá de tu círculo directo | Feed de descubrimiento tipo swipe, rankings por subgénero, búsqueda mejorada |
| **Fase 3 — Monetización** | Empezar a generar ingresos reales | Integración de anuncios, fondo compartido de ingresos, dashboard de transparencia para autores |
| **Fase 4 — Comunidad avanzada** | Profundizar el diferenciador de nicho | Glosario/wiki por novela, gamificación de lectura (XP), eventos en vivo, moneda social |

No avances de fase hasta que la anterior esté funcionando de verdad con usuarios reales, no solo "código que compila".

---

## 2. Vida del software (ciclo de vida y mantenimiento)

### 2.1 Etapas del ciclo de vida

1. **Prototipo interno** (semanas 1-4): tú y máximo 2-3 personas de confianza probando, sin usuarios externos. Objetivo: que el flujo básico funcione sin errores críticos.
2. **Beta cerrada** (Fase 0): tu grupo de WhatsApp, autores fundadores. Aquí recolectas feedback real y ajustas antes de abrir al público.
3. **Lanzamiento público suave**: abres registro sin invitación, pero sin campaña de marketing agresiva — dejas que el boca a boca de tus autores fundadores traiga tráfico orgánico.
4. **Operación y crecimiento**: monitoreo activo, arreglo de bugs reportados, features de fases 1-4 según feedback real, no según lo que "suena bien".

### 2.2 Mantenimiento continuo (esto es lo que se te va a olvidar si no lo planeas)

- **Backups automáticos de base de datos** — configúralo desde el día 1, no cuando ya perdiste datos
- **Monitoreo de errores** (herramienta gratuita: Sentry, tier gratis es suficiente al inicio)
- **Monitoreo de uptime** (UptimeRobot, gratis, te avisa si el sitio se cae)
- **Actualizaciones de dependencias** — cada 1-2 meses revisar que librerías no tengan vulnerabilidades de seguridad
- **Moderación de contenido** — vas a necesitar reglas claras y un panel donde puedas banear/ocultar contenido rápido, sin depender de acceso a la base de datos directamente

---

## 3. Arquitectura recomendada

### 3.1 Decisión clave: Monolito modular, NO microservicios

Ya hablamos de esto con el ejemplo de startups que sobre-construyen infraestructura para un tráfico que no tienen. Para un solo desarrollador con tiempo limitado, microservicios son **el error más común y más caro** que puedes cometer — multiplican la complejidad operativa (múltiples despliegues, comunicación entre servicios, monitoreo distribuido) sin darte ningún beneficio real hasta que tengas tráfico masivo y/o un equipo grande.

**Recomendación: un monolito modular.** Un solo backend, organizado en módulos claros internamente (usuarios, novelas, capítulos, comentarios, moderación), pero que se despliega como una sola aplicación. Cuando (si) algún día lo necesites, puedes separar módulos en servicios independientes — pero no antes de necesitarlo de verdad.

### 3.2 Componentes de la arquitectura

```
[Cliente web/móvil]
        │
        ▼
[Cloudflare CDN/proxy] ── cachea contenido estático, protege contra ataques básicos
        │
        ▼
[Aplicación monolítica] ── maneja auth, lógica de negocio, API
        │
        ├──▶ [Base de datos PostgreSQL] ── usuarios, novelas, capítulos, comentarios
        ├──▶ [Almacenamiento de archivos] ── portadas e imágenes (Cloudflare R2 o S3)
        └──▶ [Servicios externos] ── email transaccional, analítica, (futuro: anuncios/pagos)
```

---

## 4. Stack tecnológico — DECISIÓN FINAL

**Stack elegido: Django + Tailwind CSS + HTMX**

Razón de la elección: como desarrollador amateur en seguridad de servidores, la prioridad es un framework que traiga protecciones activadas por defecto (CSRF, prevención de inyección SQL vía ORM, hash seguro de contraseñas, protección XSS en templates) en vez de tener que configurarlas manualmente. Django resuelve esto de fábrica. Tailwind + HTMX permiten lograr una interfaz moderna e interactiva sin separar el proyecto en dos aplicaciones (backend API + frontend React), lo cual reduce la superficie de mantenimiento para un solo desarrollador.

### Componentes del stack

- **Backend**: Django (Python) — maneja modelos de datos, lógica de negocio, autenticación, panel de administración
- **Frontend**: Django templates + Tailwind CSS para estilos modernos
- **Interactividad**: HTMX — permite likes, comentarios en vivo, formularios sin recarga de página, sin necesidad de construir una SPA completa en React
- **Base de datos**: PostgreSQL
- **Hosting**: Railway o Render (deploy sencillo, tier gratis/barato para empezar)
- **Almacenamiento de imágenes**: Cloudflare R2 (compatible con S3, económico)
- **Ruta de escalamiento futuro**: si algún día se necesita más interactividad tipo app (el feed swipe, por ejemplo), se puede migrar partes específicas a Django REST Framework + React sin reescribir todo el proyecto — pero no antes de que la plataforma lo justifique con tráfico y necesidad real

### 4.1 Estructura sugerida de apps de Django

Django organiza el proyecto en "apps" (módulos independientes dentro del mismo monolito). Para este proyecto:

```
proyecto_novelas/
├── accounts/        # registro, login, perfiles de usuario (autor/lector)
├── novels/          # modelos de novela: título, sinopsis, portada, género, rating
├── chapters/        # capítulos, orden, programación de publicación
├── reading/         # biblioteca personal, seguir autores, progreso de lectura
├── comments/        # comentarios por capítulo, moderación
├── moderation/       # herramientas de moderación de contenido (reportes, baneos)
└── core/            # configuración base, utilidades compartidas
```

Cada app tiene sus propios modelos, vistas y templates — esto mantiene el código ordenado conforme crece, sin necesidad de separar en microservicios. El panel de administración de Django (`/admin`) va a leer automáticamente los modelos de cada app, dándote gestión completa de usuarios, novelas, capítulos y moderación desde el primer día, sin construir ninguna pantalla de admin a mano.

---

## 5. Herramientas de gestión del proyecto (para ti solo)

- **Control de versiones**: Git + GitHub (repositorio privado hasta que decidas abrir código o no)
- **Gestión de tareas/roadmap**: Notion o GitHub Projects — un tablero simple tipo Kanban (Por hacer / Haciendo / Hecho) por fase
- **Documentación técnica**: un archivo `docs/` en el propio repositorio con decisiones de arquitectura, para que en 6 meses no se te olvide por qué elegiste algo
- **Diseño/mockups**: Figma (gratis para proyectos personales) antes de construir pantallas, te ahorra reescribir UI
- **Comunicación con autores fundadores**: tu grupo de WhatsApp actual está bien para esta etapa, no necesitas herramienta especializada todavía

---

## 6. Presupuesto estimado de infraestructura (Fase 0-1)

| Servicio | Costo aproximado/mes |
|---|---|
| Hosting (Vercel/Railway/Render, tier inicial) | $0 - $20 |
| Base de datos administrada | $0 - $15 |
| Almacenamiento de imágenes (Cloudflare R2) | $0 - $5 (muy barato por GB) |
| Dominio propio | ~$1/mes (pagado anual) |
| Email transaccional (Resend, SendGrid tier gratis) | $0 |
| Monitoreo (Sentry, UptimeRobot tier gratis) | $0 |
| **Total estimado Fase 0-1** | **$5 - $40/mes** |

Este rango se mantiene bajo mientras tengas cientos o pocos miles de usuarios activos — coherente con lo que vimos de Royal Road operando con equipo mínimo.

---

## 7. Próximos pasos sugeridos

1. ~~Decidir entre Next.js y Django~~ — **Decidido: Django + Tailwind + HTMX**
2. Definir el modelo de datos inicial (usuarios, novelas, capítulos, comentarios) antes de escribir código, usando la estructura de apps de la sección 4.1
3. Configurar repositorio + hosting + base de datos vacía (esqueleto del proyecto)
4. Instalar y configurar Tailwind CSS dentro del proyecto Django, y HTMX vía CDN o paquete
5. Construir el flujo mínimo: registro → crear novela → subir capítulo → leer capítulo
6. Invitar a 2-3 personas de tu grupo de WhatsApp a probar el prototipo interno, antes de la beta cerrada completa
