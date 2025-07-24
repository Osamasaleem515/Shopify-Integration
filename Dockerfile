FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install spaCy model
RUN python -m spacy download en_core_web_md

# Copy project
COPY . .

# Run as non-root user
RUN useradd -m appuser
USER appuser

# Command to run
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "shopify_integration.wsgi:application"] 