FROM node:20-alpine AS build
WORKDIR /app
ARG NEXT_PUBLIC_TRACKFLOW_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_TRACKFLOW_API_URL=$NEXT_PUBLIC_TRACKFLOW_API_URL
COPY uis/backoffice/package*.json ./uis/backoffice/
COPY packages/shared ./packages/shared
RUN cd /app/uis/backoffice && npm install
COPY . .
WORKDIR /app/uis/backoffice
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ARG NEXT_PUBLIC_TRACKFLOW_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_TRACKFLOW_API_URL=$NEXT_PUBLIC_TRACKFLOW_API_URL
COPY --from=build --chown=node:node /app/uis/backoffice .
USER node
EXPOSE 3000
CMD ["npm", "start"]
