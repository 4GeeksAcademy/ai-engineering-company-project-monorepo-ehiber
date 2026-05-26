FROM node:20-alpine AS build
WORKDIR /app
COPY uis/application/package*.json ./uis/application/
RUN cd /app/uis/application && npm install
COPY . .
WORKDIR /app/uis/application
RUN npm run build

FROM nginx:stable-alpine
COPY --from=build /app/uis/application/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
