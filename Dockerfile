# Use an official Python base image
FROM Python:3.10.12

#Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt
RUN Pip install --no-cache-dir -r requirements.txt

# Copy the project files into the container 
COPY . . 

# Default Command
CMD ["python", "app.py"]
