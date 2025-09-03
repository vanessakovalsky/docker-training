FROM node:16-alpine
WORKDIR /app
RUN npm init -y && npm install express winston winston-elasticsearch
COPY web.js .
CMD ["node", "web.js"]