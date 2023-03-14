# Lab 2: First containers with CLI

## Fetch an image from Docker hub

- Fetch alpine's image from docker hub:
```
docker image pull alpine
```
- List images to verify that image has been downloaded :
```
docker image ls
```
- Launch the alpine container with the ls command to see what it contains :
```
docker container run alpine ls -l
```

## Container instances

- Show a "Welcome to alpine" message when launching the container :
```
docker container run alpine echo "Bienvenue depuis alpine"
```
- Launch a terminal in our container :
```
docker container run alpine /bin/sh
```
- Launch a container in interactive mode :
```
docker container run -it alpine /bin/sh
```
- List containers :
```
docker container ls -a
```
- How many containers are present ?

## Container insulation :

- Let's add a new container based on alpine, this time calling the ash shell :
```
docker container run -it alpine /bin/ash
```
- You can now type commands in your container:
```
echo "bienvenue" > hello.txt
ls
```
- What files appear ?

- Now let's try once out of the container terminal (exit), to display the container files :
```
docker container run alpine ls
```
- What do you notice ?
- -> This is docker isolation between host machine and containers, files are not accessible from outside

- Let's launch our container again :
```
docker container ls -a
docker container start <containerID>
```
- Tip: you can use only the first characters of the id for the containerID
- Now that the container is started we can execute inside the ls command with exec :
```
docker container exec <containerID> ls
```
- Our hello.txt file appears well!

## Container cleaning

- This first exercise being finished, we will clean our container instances :
```
docker system prune
```
