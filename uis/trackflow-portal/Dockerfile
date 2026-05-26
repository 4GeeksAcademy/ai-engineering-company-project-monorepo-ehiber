FROM node:20-alpine AS build
WORKDIR /app
COPY uis/trackflow-portal/package*.json ./uis/trackflow-portal/
COPY packages/shared ./packages/shared
COPY internal/trackflow-coding-fundamentals ./uis/trackflow-coding-fundamentals
RUN cd /app/uis/trackflow-portal && npm install
COPY . .
WORKDIR /app/uis/trackflow-portal
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/uis/trackflow-portal .
EXPOSE 3000
CMD ["npm", "start"]
