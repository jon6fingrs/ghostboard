# Use a lightweight Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy the server files
COPY get_text.py /app/
COPY index.html /app/
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080
EXPOSE 8080

# Run the server
CMD ["python", "/app/get_text.py"]
