# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependencies first (for caching)
COPY requirements.txt .


# Install dependencies including PyJWT
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the entire application
COPY . .

# Copy .env file into the container
COPY .env /app/.env


# Expose the correct Cloud Run port
EXPOSE 8080

# Set environment variables
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production
ENV PORT=8080  

# Ensure Gunicorn is installed (if missing)
RUN pip install gunicorn

# Run the Flask app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "--timeout", "0", "main:app"]