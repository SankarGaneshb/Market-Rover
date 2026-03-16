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

# Copy backend code
COPY backend/src /app/backend/src

# Copy frontend build output from stage 1 into the backend container
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose Cloud Run port
EXPOSE 8080
ENV PORT=8080

# Run the Uvicorn server from the backend directory
WORKDIR /app/backend
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8080"]
