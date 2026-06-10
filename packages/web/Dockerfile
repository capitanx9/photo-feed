# syntax=docker/dockerfile:1
#
# Multi-stage build for the Next.js (App Router) web app.
# Relies on `output: "standalone"` in next.config.ts, which makes Next
# emit a self-contained runtime under .next/standalone/.

FROM node:22-alpine AS deps
WORKDIR /app
COPY packages/web/package.json packages/web/package-lock.json* ./
# `npm ci` falls back to install when no lockfile is present (we keep
# package-lock.json in the repo so it should always be a ci).
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# ---------------------------------------------------------------------
FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY packages/web ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ---------------------------------------------------------------------
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Run as a non-root user. Next standalone is a plain Node process; no
# privileged operations needed at runtime.
RUN addgroup --system --gid 1001 nodejs \
 && adduser  --system --uid 1001 nextjs

# Standalone runtime: .next/standalone has server.js + minimal node_modules
# inlined. The public/ folder and .next/static must be copied alongside —
# Next reads them from process.cwd() at runtime.
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
