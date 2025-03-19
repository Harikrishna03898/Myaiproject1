#First Stage
# Python version
FROM python:3.11-slim AS base

# Healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && apt-get clean

# working directory
WORKDIR /app

# Copying only requirements file first for better caching
COPY requirements.txt /app

# Installing dependencies and also for reducing caching
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . /app/

# Expose the application's port
EXPOSE 5000

#Second Stage
FROM base AS Final
WORKDIR /app
COPY requirements.txt /app
COPY . /app/
CMD ["python", "chatapp.py"]