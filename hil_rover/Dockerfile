# Stage 1: Build the React Frontend
FROM node:22-bullseye AS frontend-builder

WORKDIR /app/frontend
COPY hil_rover/frontend/package*.json ./
RUN npm ci

COPY hil_rover/frontend/ .
RUN npm run build

# Stage 2: Build the FastAPI Backend
FROM python:3.13-slim

WORKDIR /app

# Install Backend Dependencies
COPY hil_rover/backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy root dependencies needed for agents
COPY agents.py config.py ./
COPY rover_tools/ ./rover_tools/
COPY utils/ ./utils/
COPY scripts/ ./scripts/

# Copy entire backend directory
COPY hil_rover/backend/ ./backend/
RUN mkdir -p /app/data && chmod 777 /app/data

# Copy frontend build output from stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose Cloud Run port
EXPOSE 8080
ENV PORT=8080
# Set PYTHONPATH so internal imports from root (scripts, agents) work
ENV PYTHONPATH=/app

# Point to frontend
ENV HIL_FRONTEND_PATH=/app/frontend/dist

# Run from /app/backend so 'src' is findable
WORKDIR /app/backend

# Use uvicorn to serve the API
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8080"]
