# =============================================================================
# Frontend Dockerfile - Multi-Stage Build
# =============================================================================
# Stage 1: Dependencies - Install npm packages
# Stage 2: Builder - Build Next.js application
# Stage 3: Production - Minimal runtime image
# =============================================================================

# Stage 1: Dependencies
FROM node:20-alpine AS deps

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install all dependencies (including devDependencies for build)
RUN npm install

# -----------------------------------------------------------------------------
# Stage 2: Builder
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build-time API URL (NEXT_PUBLIC_* is inlined at build time; optional for non-Minikube builds)
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Set environment for build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build application
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 3: Production
FROM node:20-alpine

WORKDIR /app

# Set environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Copy necessary files from builder (use existing 'node' user from base image)
# Note: public folder is optional, some Next.js projects don't have it
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static

# Switch to non-root user (node user already exists in alpine with UID 1000)
USER node

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:3000/api/health || exit 1

# Start application
CMD ["node", "server.js"]
