# Lab 3 - Create a BDD container with a volume and a web container with exposing a port

## Prerequisites

- Clone the repository to your machine :     
git clone https://github.com/dockersamples/linux_tweet_app
- Create a login on the docker hub :
https://hub.docker.com/ 

## Lancement de conteneur ubuntu et mysql
- To start we launch an ubuntu container in interactive mode and we ask it to launch the bash process :
```
 docker container run --interactive --tty --rm ubuntu bash
```
- You then have access to the ubuntu container terminal :
```
root@<container id>:/#
```
- We can then launch standard linux commands :
```
ls
ps aux
cat /etc/issue
```
- To get out of bash's container : 
```
exit
```
- Now let's move on to the mysql container
```
 docker container run -i \
 --detach \
 --name mydb \
 -e MYSQL_ROOT_PASSWORD=my-secret-pw \
 mysql:latest
 ```
 - We use the detach mode to run the container in the background, we give it a name and we pass it as an environment parameter the root password of mysql that we want to define, then we use the image mysql:latest
 - We check that the container has launched in detached mode :
```
  docker container ls
```
- To access container's log and find out what's going on :
```
docker container logs mydb
```
- To see current processes in our container :
```
docker container top mydb
```
- To get the version of mysql used in our container :
```
docker exec -it mydb \
 mysql --user=root --password=$MYSQL_ROOT_PASSWORD --version
```
- We will then create a database using commands in the mydb container
```
 docker exec -it mydb sh
```
- Then once in the terminal we created our database
```
 mysql --user=root --password=$MYSQL_ROOT_PASSWORD 
```
 - Once in mysql terminal : 
```
 CREATE DATABASE mydb;
 exit 
```
- We get out of our container :
```
 exit 
```

## Create volume and attach it to our container
- Create volume
```
docker volume create --name myvolume
```
- Save the image of our mysql container and commit it
```
docker commit <containerID> newimagename
```
- Launch a new container by attaching our volume to our container
```
docker run -ti -v myvolume:/chemin/vers/mysqldata newimagename /bin/bash
```

## Expose port 80 on our container

- Launch an Ubuntu container running in the background :
```
docker container run -t -d ubuntu

```
- This one brings you the ID of the container to use in the following commands

- Install Apache on our container Ubuntu :
```
docker container exec -t -i <containerID> '/bin/bash'
root@<containerID>:$ apt -y update && apt install -y apache2 
root@<containerID>:$ service apache2 start
```
- Records the image of our Ubuntu container and commit it
```
docker commit <containerID> newimagename2
```
- Expose Port 80
```
docker container run -i --detach -p 80:80 newimagename2
```

## Create an assembly with the shared folder :

- we Will Now Set Up The File In Which We Have Recovered The GitHub Depot On Our Container (first Place Ourselves In The Folder Where Is The Depot Code)

```
docker run -d -it --name devtest --mount type=bind,source="$(pwd)",target=/var/www/html/myapp -p 8090:80 newimagename2
```

* Connect to the container and start Apache

```
docker exec -it devtest /bin/bash
root@idducontainer: service apache2 start
exit
```
- Local (where Docker is installed) open a browser and go to http://localhost:8090/MyApp

## Modify a file

- On your hote machine, modify the index.html file
- Recharge your web page with the URL of your LAB: your changes should appear

## Push your images
- Connect to the Docker Hub by using :
```
docker login --username=yourhubusername 
```
- Tag your image :
```
docker tag <imageId> yourhubusername/newimagename2:firsttry
```
- Push your images on the repository :
```
docker push yourhubusername/newimagename2:firsttry
```

-> Well played you have finished this lab
