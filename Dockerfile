FROM python:3.9-slim

ENV PORT=5001

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the necessary dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on (default Flask port is 5000)
EXPOSE $PORT

# Run the app
# CMD ["python", "app.py"]
CMD gunicorn --bind 0.0.0.0:$PORT app:app
