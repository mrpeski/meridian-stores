FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json /app/
RUN npm ci

COPY index.html vite.config.ts tsconfig.json /app/
COPY src /app/src

# Relative `/api/*` in the bundle; nginx proxies at runtime (see `nginx.conf`).
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
