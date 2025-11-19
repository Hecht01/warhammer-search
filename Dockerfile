FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY ./api ./api
COPY ./indexing ./indexing
COPY ./static ./static

# Expose port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "api.search:app", "--host", "0.0.0.0", "--port", "8000"]
