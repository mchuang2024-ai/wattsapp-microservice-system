FROM node:20-alpine

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* frontend/pnpm-lock.yaml* ./
RUN npm install

COPY frontend/. ./

RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
