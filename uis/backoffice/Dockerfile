FROM node:20-alpine AS build
WORKDIR /app
COPY uis/backoffice/package*.json ./uis/backoffice/
COPY packages/shared ./packages/shared
RUN cd /app/uis/backoffice && npm install
COPY . .
WORKDIR /app/uis/backoffice
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/uis/backoffice .
EXPOSE 3000
CMD ["npm", "start"]