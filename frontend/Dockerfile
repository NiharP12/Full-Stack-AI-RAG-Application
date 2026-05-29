# =========================================================
# Frontend Dockerfile — Multi-stage build
# =========================================================

# ---- Build stage ----
FROM node:22-slim as builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the Angular application for production
RUN npm run build -- --configuration production

# ---- Production stage ----
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist/frontend/browser /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
