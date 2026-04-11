# Stage 1: Build the React Frontend
FROM node:22-bullseye AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# Stage 2: Build the FastAPI Backend
FROM python:3.11-slim

WORKDIR /app

# Install Backend Dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy entire backend directory
COPY backend/ ./backend/

# Create data directory for persistent logs
RUN mkdir -p /app/data && chmod 777 /app/data

# Copy frontend build output from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose Cloud Run port
EXPOSE 8080
ENV PORT=8080

# Run from /app/backend so 'src' is findable
WORKDIR /app/backend

# Use uvicorn to serve the API
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8080"]
