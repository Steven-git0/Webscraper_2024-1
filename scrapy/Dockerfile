# Use an official Python runtime as a base image
FROM python:3.12

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Scrapy if it's not listed in your requirements.txt
RUN pip install scrapy 

# Run the Scrapy spider using CMD
# Replace `my_spider` with your spider name
CMD ["scrapy", "crawl", "wcdspider"]
