FROM node:20-alpine AS build
WORKDIR /app
COPY uis/talent-pipeline-tracker/package*.json ./uis/talent-pipeline-tracker/
COPY packages/shared ./packages/shared
RUN cd /app/uis/talent-pipeline-tracker && npm install
COPY . .
WORKDIR /app/uis/talent-pipeline-tracker
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/uis/talent-pipeline-tracker .
EXPOSE 3000
CMD ["npm", "start"]
