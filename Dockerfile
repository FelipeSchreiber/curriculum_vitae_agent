FROM python:3.11.4-slim

WORKDIR /app

COPY . /app/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
RUN python -m pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# Expose default Gradio port
EXPOSE 7860

# Set environment variable for Gradio server name to be accessible from outside
ENV GRADIO_SERVER_NAME="0.0.0.0"

CMD ["python","main.py"]
