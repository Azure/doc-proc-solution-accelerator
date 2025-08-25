FROM mcr.microsoft.com/devcontainers/python:dev-3.12

RUN apt-get update && apt-get install -y build-essential
RUN apt-get install unixodbc -y
RUN apt-get install ca-certificates -y
RUN update-ca-certificates 

COPY ./ui-template /
 
# Expose the port your app runs on
EXPOSE 80
 
# Define the command to run your app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]