# Start from an official Python image (slim = smaller download)
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy and install dependencies FIRST (before copying app code)
# Docker caches each step — if requirements.txt hasn't changed,
# it skips the slow pip install and jumps straight to copying your code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the app
COPY . .

# Tell Docker which port this service listens on (documentation only —
# the actual binding happens in the uvicorn command below)
EXPOSE 8001

# Start the server
# --reload    = auto-restart when you change a file (dev only)
# --host 0.0.0.0 = listen on all network interfaces inside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
