# ---------- Build Stage ----------
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

RUN npm run build


# ---------- Runtime Stage ----------
FROM nginx:alpine

# Templates in this directory are run through envsubst on container start.
# The filter keeps substitution to API_TOKEN so nginx's own $host,
# $remote_addr etc. are left alone.
COPY default.conf.template /etc/nginx/templates/default.conf.template
ENV NGINX_ENVSUBST_FILTER="API_TOKEN"

COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

RUN chmod -R 755 /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]