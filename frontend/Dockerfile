# Phase 01 template: requires package.json, package-lock.json and a Vite app.
FROM node:22-bookworm-slim AS development
WORKDIR /app
COPY --chown=node:node . .
RUN npm ci
USER node
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM development AS build
ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginxinc/nginx-unprivileged:stable-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
