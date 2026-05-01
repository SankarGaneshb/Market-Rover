FROM node:22-bullseye AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
# Use sed to replace the placeholder BACKEND_URL with the environment variable at runtime
CMD ["/bin/sh", "-c", "sed -i \"s|BACKEND_URL|$BACKEND_URL|g\" /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'"]
