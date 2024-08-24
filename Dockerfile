# AcademicHustlerBot Dockerfile

# Use Python 3.11 image
FROM python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt to working directory
COPY requirements.txt /app

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy current directory contents to /app within the container
COPY . .

# Set environment variables
ENV PYTHONPATH /app/src

# Command to run the bot
CMD ["python", "/app/src/main.py"]
