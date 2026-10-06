# Tadabbur web frontend
#
#   docker build --target production -t tadabbur-frontend .
#   docker build --target production --build-arg VITE_API_URL=https://api.example.org -t ... .
#
# VITE_API_URL is a public build-time value (empty = same origin, /api is
# proxied by nginx). Never pass a secret as a build arg: VITE_* values are
# compiled into the public JavaScript bundle.

ARG NODE_IMAGE=node:20-alpine
ARG NGINX_IMAGE=nginxinc/nginx-unprivileged:1.27-alpine

# ------------------------------------------------------------------- deps
FROM ${NODE_IMAGE} AS deps
WORKDIR /app
COPY package.json package-lock.json ./
# Optional build secret "extra_ca" for builds behind a TLS-intercepting proxy
# (mounted for this step only, never stored in a layer).
RUN --mount=type=secret,id=extra_ca \
    if [ -s /run/secrets/extra_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/extra_ca; fi; \
    npm ci --no-audit --no-fund

# ------------------------------------------------------------ development
# Used by docker-compose.portable.yml for local work only (Vite dev server).
FROM ${NODE_IMAGE} AS development
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ---------------------------------------------------------------- builder
FROM ${NODE_IMAGE} AS builder
WORKDIR /app
ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL} NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ------------------------------------------------------------- production
# nginx as an unprivileged user (uid 101), listening on 8080.
FROM ${NGINX_IMAGE} AS production
COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx-security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1:8080/health || exit 1
CMD ["nginx", "-g", "daemon off;"]
