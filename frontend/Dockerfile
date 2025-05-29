# frontend.Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY frontend/ /app/

RUN npm install
RUN npm run build

# Serve using a static server
RUN npm install -g serve
CMD ["serve", "-s", "build", "-l", "3000"]
