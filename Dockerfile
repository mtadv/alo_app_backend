# Use an official Python base image
FROM python:3.10-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set working directory
WORKDIR /app

# Copy all project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose the port your app runs on
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
