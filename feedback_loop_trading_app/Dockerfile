FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY src/ ./src/

# Copy the environment variable example
COPY .env.example .env

# Expose the necessary port (if applicable)
EXPOSE 8000

# Command to run the application
CMD ["python", "src/main.py"]