# Use a lightweight Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy the client files
COPY text_client.py /app/
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Define the command
ENTRYPOINT ["python", "/app/text_client.py"]
