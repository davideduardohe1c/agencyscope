# Publicar AgencyScope V3 online

Esta carpeta ya está preparada para despliegue público.

## Opción recomendada: Render + GitHub

### 1. Crea un repositorio en GitHub
Crea un repositorio nuevo, por ejemplo:

`agencyscope`

Sube **el contenido de esta carpeta** al repositorio.

La estructura debe verse así:

```text
agencyscope/
├── app.py
├── requirements.txt
├── render.yaml
├── Procfile
├── .python-version
├── templates/
│   └── index.html
└── static/
    ├── logo.svg
    └── favicon.svg
```

No subas la carpeta `.venv`.

### 2. Entra a Render
Crea una cuenta o inicia sesión y selecciona:

**New → Web Service**

Conecta GitHub y selecciona el repositorio `agencyscope`.

### 3. Configuración
Render normalmente podrá leer `render.yaml`.

Si te pide los campos manualmente:

**Language / Runtime**
```text
Python 3
```

**Build Command**
```text
pip install -r requirements.txt
```

**Start Command**
```text
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

### 4. Deploy
Pulsa **Create Web Service / Deploy**.

Cuando termine, Render te dará una URL parecida a:

```text
https://agencyscope.onrender.com
```

Esa es la URL que puedes enviarle al profesor.

---

## Verificar que funciona

Abre:

```text
https://TU-URL.onrender.com/health
```

Debe responder algo similar a:

```json
{"ok": true, "service": "AgencyScope V3"}
```

Después abre la URL principal.

---

## Actualizaciones futuras

Si el servicio está conectado a GitHub, los nuevos cambios que subas al repositorio pueden volver a desplegarse desde Render.

---

## Railway

La carpeta incluye también un `Procfile` y una configuración compatible con Gunicorn.

En Railway:

1. New Project
2. Deploy from GitHub repo
3. Selecciona el repositorio
4. Si Railway no detecta el inicio automáticamente, usa:

```text
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

5. En Settings → Networking, genera el dominio público.

---

## Nota sobre scraping / investigación pública

AgencyScope consulta sitios externos durante los análisis.

Algunas webs pueden:
- bloquear requests automatizados,
- responder más lento desde un hosting cloud,
- mostrar información distinta por región,
- aplicar rate limits.

Eso no significa necesariamente que AgencyScope esté caído. La herramienta debe seguir mostrando los competidores que sí pudo analizar.
