FROM python:3.11-slim

# Set work directory
WORKDIR /app


# # Install system dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*


# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# Copy project
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

