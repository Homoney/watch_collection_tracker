FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create uploads directory
RUN mkdir -p /usr/share/nginx/uploads

# Create non-root user and set ownership
RUN addgroup -S appgroup && \
    adduser -S -G appgroup appuser && \
    chown -R appuser:appgroup /usr/share/nginx && \
    chown -R appuser:appgroup /var/cache/nginx && \
    chown -R appuser:appgroup /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appgroup /var/run/nginx.pid

# Switch to non-root user
USER appuser

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
