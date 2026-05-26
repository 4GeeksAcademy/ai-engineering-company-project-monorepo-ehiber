FROM node:20-alpine AS build
WORKDIR /app
COPY uis/web/package*.json ./uis/web/
RUN cd /app/uis/web && npm install
COPY . .
WORKDIR /app/uis/web
RUN npm run build

FROM nginx:stable-alpine
COPY --from=build /app/uis/web/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
