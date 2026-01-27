FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create uploads directory
RUN mkdir -p /usr/share/nginx/uploads

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
