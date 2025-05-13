
# Base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY fastapi_dalva_app.py .

# Expose port
EXPOSE 8000

# Run the API
CMD ["uvicorn", "fastapi_dalva_app:app", "--host", "0.0.0.0", "--port", "8000"]
