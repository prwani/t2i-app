FROM node:20-alpine

ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000

ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

WORKDIR /app

COPY web/package*.json ./
RUN npm ci

COPY web ./
RUN npm run build \
    && npm prune --omit=dev

EXPOSE 3000

CMD ["npm", "start"]
