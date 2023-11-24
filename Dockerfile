FROM python:3.11-slim

# See: http://label-schema.org/
LABEL org.label-schema.author="Charle Demers" \
      org.label-schema.vendor="Wellington and King inc." \
      org.label-schema.name="TFDriftAgent" \
      org.label-schema.description="A simple agent to detect and report drift in Terraform projects." \
      org.label-schema.vcs-url=https://github.com/cdemers/TFDriftAgent \
      org.opencontainers.image.source=https://github.com/cdemers/TFDriftAgent

# Install Git and clean up the cache in a single RUN command to keep the layer small
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container at /usr/src/app
COPY src/requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /usr/src/app
COPY src/ .

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python", "agent.py"]
