# Stage 1: Build Stage
FROM node:20 as build-stage

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install --production

# Copy source files
COPY index.js ./

# Stage 2: Final Stage
FROM public.ecr.aws/lambda/nodejs:20

# Copy necessary files from the build stage
COPY --from=build-stage /app /var/task/

# Set the CMD to your handler
CMD [ "index.handler" ]
