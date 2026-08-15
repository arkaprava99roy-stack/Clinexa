# ============================================================
# Clinexa Frontend — Dockerfile (Development)
# ============================================================
FROM node:20-alpine AS base

WORKDIR /app

# Install deps first (layer caching)
COPY package.json package-lock.json* ./
RUN npm ci

# Copy app source
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
