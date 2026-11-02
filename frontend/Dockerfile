FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Dev server (docker compose). Source is bind-mounted over /app.
FROM deps AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]

FROM deps AS build
COPY . .
RUN npm run build

# Static build for Kubernetes staging. /api and /graphql are routed by the ingress.
FROM nginx:1.27-alpine AS prod
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80

# Production on a single VM: Caddy serves this build and proxies the API (infra/Caddyfile).
FROM caddy:2-alpine AS web
COPY --from=build /app/dist /srv
