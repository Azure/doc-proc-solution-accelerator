FROM mcr.microsoft.com/devcontainers/python:dev-3.12

RUN apt-get update && apt-get install -y build-essential
RUN apt-get install unixodbc -y

COPY . /

#RUN python3 -m venv ~/pyvenv --system-site-packages
#RUN . ~/pyvenv/bin/activate
RUN pip install -r requirements.txt 

# Expose the port your app runs on
EXPOSE 80
 
# Define the command to run your app
CMD ["uvicorn", "worker:app", "--host", "0.0.0.0", "--port", "80"]