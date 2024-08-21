# Use the full official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl gnupg2 apt-transport-https build-essential libssl-dev libffi-dev python3-dev && \
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl -sSL https://packages.microsoft.com/config/debian/11/prod.list -o /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt /app/

# Create the virtual environment
RUN python3 -m venv /opt/venv

# Upgrade pip inside the virtual environment
RUN /opt/venv/bin/pip install --upgrade pip

# Install Python dependencies from requirements.txt
RUN /opt/venv/bin/pip install -r /app/requirements.txt

# Copy the rest of the application code
COPY . /app

# Make sure the venv binaries are available in the path
ENV PATH="/opt/venv/bin:$PATH"

# Expose port 8000 for the app
EXPOSE 8000

# Command to run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
