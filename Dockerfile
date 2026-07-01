FROM python:3.12-slim AS builder

# Install Node.js
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Backend Python Dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install Frontend Node Dependencies and Build
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm ci

# Copy all source code
COPY backend ./backend
COPY frontend ./frontend

# Build Frontend (Standalone)
RUN cd frontend && npm run build

# ---
# Final Stage
# ---
FROM python:3.12-slim

WORKDIR /app

# Install Node.js runtime (no build tools needed)
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy backend code
COPY backend ./backend

# Copy Next.js standalone build
# Next.js copies everything needed into standalone, including node_modules
COPY --from=builder /app/frontend/.next/standalone ./frontend
COPY --from=builder /app/frontend/.next/static ./frontend/.next/static
COPY --from=builder /app/frontend/public ./frontend/public

# Copy start script
COPY start.sh ./
RUN chmod +x start.sh

# Render uses the PORT env variable
ENV PORT=10000
EXPOSE 10000

CMD ["./start.sh"]
