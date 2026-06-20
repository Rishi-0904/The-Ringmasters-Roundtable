# Use a lightweight Node base image
FROM node:20-alpine

# Set the working directory
WORKDIR /usr/src/app

# Install curl in alpine for healthcheck support
RUN apk add --no-cache curl

# Copy dependency manifests
COPY package*.json ./

# Install only production dependencies
RUN npm ci --only=production

# Copy backend source files
COPY . .

# Expose port 3000
EXPOSE 3000

# Start server
CMD ["node", "server.js"]
