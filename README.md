# Librachieve

Gestor de biblioteca personal de videojuegos: importa tus juegos de Steam, Epic, GOG y Amazon, organízalos por categorías y consulta tus estadísticas.

## Arranque rápido

Requisitos: Docker Desktop.

```bash
cp .env.example .env        # rellena las claves (ver abajo)
docker compose -f infra/docker-compose.yml up -d --build
```

- App: http://localhost:5173
- Documentación de la API: http://localhost:5173/api/docs
- GraphQL (GraphiQL): http://localhost:5173/graphql

Las migraciones se aplican solas al arrancar el backend.

## Claves externas

| Variable | Para qué | Dónde se consigue |
|---|---|---|
| `STEAM_API_KEY` | Importar la biblioteca de Steam y el avatar/nombre | https://steamcommunity.com/dev/apikey |
| `IGDB_CLIENT_ID` / `IGDB_CLIENT_SECRET` | Portadas, géneros, fechas y descripciones | Crea una app en https://dev.twitch.tv/console/apps |
| `SECRET_KEY` | Firma de los JWT | Cualquier cadena aleatoria de 32+ caracteres |

Sin estas claves la app funciona igual: se puede iniciar sesión con Steam y hacer importaciones manuales, pero no habrá sincronización con Steam ni metadatos. Cuando añadas las claves de IGDB, los juegos sin metadatos se completarán en la siguiente importación.

## Arquitectura

```
navegador ──► Vite (dev) / Ingress (k8s) / CloudFront (prod)
                 ├── /            → SPA React
                 ├── /api/*       → FastAPI (REST)
                 └── /graphql     → FastAPI (Strawberry, listados con filtros)
FastAPI ──► PostgreSQL (fuente de verdad)
        └─► Redis (caché IGDB 24h, refresh tokens, cola ARQ) ◄── worker ARQ (sync Steam, IGDB)
```

- **Sesión:** JWT de acceso de 15 min en memoria + refresh token rotatorio en cookie `httpOnly`, guardado en Redis y revocable.
- **Steam:** inicio de sesión con OpenID 2.0; la biblioteca se lee con `GetOwnedGames`. El usuario debe tener los «Detalles de juegos» como públicos en Steam.
- **Importación manual:** JSON o CSV con columna `title`/`name` y, opcionalmente, `playtime_minutes`/`hours`, `status`, `last_played`.

## Kubernetes (staging con Minikube)

```bash
minikube start && minikube addons enable ingress
eval $(minikube docker-env)                       # en PowerShell: minikube docker-env | Invoke-Expression
docker build -f backend/Dockerfile -t librachieve-backend:latest .
docker build --target prod -t librachieve-frontend:latest frontend
cp infra/k8s-secret.example.yaml infra/k8s/secret.yaml   # rellenar (está en .gitignore)
kubectl apply -f infra/k8s/
# añade "<minikube ip> librachieve.local" al fichero hosts
```

## Despliegue en AWS

`.github/workflows/deploy.yml` se ejecuta tras un CI verde en `main`: sube el frontend a S3 (+ invalidación de CloudFront) y despliega backend + worker en EC2 con `infra/docker-compose.prod.yml`. Necesita configurar en GitHub los secretos `AWS_ROLE_ARN`, `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY` y las variables `AWS_REGION`, `S3_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID`. Mientras `S3_BUCKET` no esté definida, el despliegue se omite.

## Desarrollo

Consulta [CLAUDE.md](CLAUDE.md) para las reglas del proyecto y los comandos de tests, migraciones y administración.
