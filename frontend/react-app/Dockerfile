# ── Multi-stage Build ─────────────────────────────────────────────────────────
# A React app needs Node.js to build, but NOT to run — the output is just
# static files (HTML, JS, CSS). Multi-stage builds let us:
#   Stage 1 (builder): use a Node image to compile the app
#   Stage 2 (runtime): use a tiny nginx image to serve the output
# The final image only contains stage 2 — node_modules (~500MB) are discarded.
# Result: ~25MB image instead of ~600MB.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Build ────────────────────────────────────────────────────────────
# AS builder gives this stage a name so we can reference it in stage 2.
# node:20-alpine: Node 20 on Alpine Linux (tiny ~50MB base).
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first (same cache trick as the backend Dockerfile).
# package-lock.json pins exact versions of every dependency.
COPY package*.json ./

# npm ci (clean install): faster than npm install, uses package-lock.json exactly.
# Preferred over npm install in Docker/CI environments.
RUN npm ci

# Copy source code and build.
COPY . .

# `npm run build` runs Vite, which bundles everything into /app/dist.
RUN npm run build


# ── Stage 2: Serve ────────────────────────────────────────────────────────────
# Start fresh from nginx:alpine (~25MB). Nothing from stage 1 carries over
# except what we explicitly COPY --from=builder.
FROM nginx:alpine

# Copy only the compiled static files from the builder stage.
# /usr/share/nginx/html is nginx's default root directory for serving files.
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our custom nginx config (handles React Router's client-side routing).
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# nginx -g "daemon off;" keeps nginx in the foreground.
# Docker requires the main process to stay in the foreground — if it exits, the container stops.
CMD ["nginx", "-g", "daemon off;"]
