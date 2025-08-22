# Use an official Python runtime as a parent image
FROM python:3.12.6-slim

# Set environment variable to ensure Python output is sent directly to the terminal (e.g., for logging)
ENV PYTHONUNBUFFERED=1

# Set the working directory to /app
WORKDIR /app

# Copy only the requirements file first to leverage Docker layer caching
COPY requirements.txt /app/

# Upgrade pip and install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the application code to the container
COPY . /app/

# Expose port 8000 for the Django development server
EXPOSE 8000

# Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
