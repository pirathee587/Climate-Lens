FROM node:22-bookworm-slim AS development
WORKDIR /app
# Install and build as the unprivileged `node` user. /app and node_modules
# must be node-owned so `tsc -b` (node_modules/.tmp) and `vite build`
# (dist/) can write in the build stage.
RUN chown node:node /app
USER node
COPY --chown=node:node package.json package-lock.json ./
RUN npm ci
COPY --chown=node:node . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM development AS build
ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginxinc/nginx-unprivileged:stable-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
