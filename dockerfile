# Use the Python3.8 container image
FROM python:3.8
# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install the dependecies
RUN pip install -r requirements.txt