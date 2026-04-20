# Updated Dockerfile

# Start from the base image
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Copy the backend directory
COPY backend/ .

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the application
CMD ["python", "-m", "backend.src.server"]
