# Plane Bridge API

API bridge entre **Plane** y **Claude Desktop**. Extrae todo el contenido de un workspace de Plane y lo devuelve como un JSON estructurado.

---

## ⚠️ API Key para Claude Desktop

```
XXXXXXXXXXXXXXXXXXX
```

Úsala en el header `X-API-Key` en todas las peticiones autenticadas.

---

## 1. Obtener el token de Plane

1. Entra a `https://plane.takumi-dev.com`
2. Ve a **Settings → API Tokens** (esquina superior derecha → tu perfil → API Tokens)
3. Haz clic en **Add API Token**
4. Ponle un nombre (ej: `plane-bridge`) y copia el token generado
5. Pégalo en el `.env` como `PLANE_API_TOKEN`

---

## 2. Configurar el `.env`

```bash
cp .env.example .env
```

Edita `.env` y completa los valores:

```env
PLANE_BASE_URL=https://plane.takumi-dev.com
PLANE_API_TOKEN=tu-token-de-plane-aqui
DEFAULT_WORKSPACE_SLUG=WORKSPACE
BRIDGE_API_KEY=XXXXXXXXXXXXXXXXXXX
```

---

## 3. Levantar con Docker

```bash
docker-compose up -d
```

Para ver los logs en tiempo real:

```bash
docker-compose logs -f
```

Para detener:

```bash
docker-compose down
```

---

## 4. Ejemplos de curl

### Health check (público)
```bash
curl http://localhost:8000/health
```

### Extraer workspace completo
```bash
curl -H "X-API-Key: XXXXXXXXXXXXXXXXXXX" \
  http://localhost:8000/workspace/WORKSPACE
```

### Solo proyectos
```bash
curl -H "X-API-Key: XXXXXXXXXXXXXXXXXXX" \
  http://localhost:8000/workspace/WORKSPACE/projects
```

### Solo issues
```bash
curl -H "X-API-Key: XXXXXXXXXXXXXXXXXXX" \
  http://localhost:8000/workspace/WORKSPACE/issues
```

---

## 5. Configurar Claude Desktop

Agrega esto al archivo de configuración de Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "plane-bridge": {
      "command": "curl",
      "args": [
        "-s",
        "-H", "X-API-Key: XXXXXXXXXXXXXXXXXXX",
        "http://localhost:8000/workspace/WORKSPACE"
      ]
    }
  }
}
```

O simplemente dile a Claude en el chat:

> "Llama a `http://localhost:8000/workspace/WORKSPACE` con el header `X-API-Key: XXXXXXXXXXXXXXXXXXX` y analiza el contenido del workspace"

---

## Estructura de la respuesta

```json
{
  "workspace": {
    "slug": "WORKSPACE",
    "name": "WORKSPACE",
    "members": [...],
    "projects": [
      {
        "id": "...",
        "name": "...",
        "states": [...],
        "labels": [...],
        "members": [...],
        "modules": [{ "id": "...", "name": "...", "issues": [...] }],
        "cycles": [{ "id": "...", "name": "...", "issues": [...] }],
        "views": [...],
        "issues": [
          {
            "id": "...",
            "name": "...",
            "state": "...",
            "priority": "...",
            "assignees": [...],
            "comments": [...],
            "sub_issues": [...],
            "due_date": "..."
          }
        ]
      }
    ]
  },
  "extracted_at": "2024-01-01T00:00:00Z",
  "total_issues": 42,
  "total_projects": 3,
  "errors": []
}
```

---

## Documentación interactiva

Con el servicio corriendo, accede a:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
