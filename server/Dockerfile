# Use a lightweight Python image
FROM python:3.12-slim

# Install nginx and supervisor
RUN apt-get update && apt-get install -y nginx supervisor && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app



# Copy the server files
COPY get_text.py /app/
COPY index.html /app/
COPY requirements.txt /app/
COPY static /app/static

RUN touch /app/static/docker_env

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Remove default config files from both directories
RUN rm -f /etc/nginx/conf.d/default.conf && rm -f /etc/nginx/sites-enabled/default

# Copy your custom configuration into the correct location
COPY ghostboard.conf /etc/nginx/conf.d/

# Copy the supervisor configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports: NGINX (80), HTTP server (8080), and WebSocket server (8765)
EXPOSE 80 8080 8765

# Start supervisor (which in turn starts nginx and the Python server)
CMD ["/usr/bin/supervisord", "-n"]

