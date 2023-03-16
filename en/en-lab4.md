# Build a personalized container

## Prerequisite :
- Recover the code in this depot (app.py and requirements.txt):
[https://github.com/eficode-academy/docker-katas/tree/master/labs/building-an-image](https://github.com/eficode-academy/docker-katas/tree/master/labs/building-an-image)

## Create the Docker File

- We will create a Dockerfile to be able to build the image necessary for the execution of the application :
    - Create a Dockerfile file (without extension) at the same level as the two files recover on the deposit
    - Open the file (all instructions will be added in the file) and add the basic image :
```
FROM ubuntu:latest
```
- Now add the installation of the necessary tools:
```
RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential
```
- Then install the libraries necessary for help and the requirements.txt file :
```
COPY requirements.txt /usr/src/app/
RUN pip3 install --no-cache-dir -r /usr/src/app/requirements.txt
```
- Then copy the application file
```
COPY app.py /usr/src/app/
```
- And exhibit port 5000 on which the application turns
```
EXPOSE 5000
```
- Finally we use CMD to launch the application
```
CMD ["python3", "/usr/src/app/app.py"]
```
- Our dockerfile is ready for the future

## Building our image
- In the folder with the Dockerfile, launch the build of builds to build the image, the -t option allows you to name the image built :
```
docker build -t myfirstapp .
```
- What happened during the build?
- Check that the image is available:
```
docker images
```

## Launch of the container with the built image
- It only remains to launch the container :
```
docker container run -p 8888:5000 --name myfirstapp myfirstapp
```
- To access the application, open Port 88888 on the host since it is this port which is mapped on port 5000 of our application (or any other port of your choice when launching the container)

## Plying images :

- Each image Building is based on several layers, that is to say several images superimposed to each other
- To see all the images used by an image :
```
docker image history <image ID>
```
- It is possible to use each of these layers since they are cache in the Docker images managers, which allows you to reuse different layers for different final images

-> Well played, this lab is finished, you can now try to create personalized containers for any application
