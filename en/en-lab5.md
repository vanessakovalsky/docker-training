# Lab 5 : A multi-container application with Docker compose

In this TP, we will contain a website that uses WordPress, so we will have two containers for this, one for Apache / PHP and one for the database which will have to communicate with each other.The website should be accessible from the outside, so we will also need to map ports.
For this we will use Docker-Concomose which allows you to launch several containers at the same time.

## Manually launch the 2 containers 
- To start we will launch a new mysql container :
```
docker container run --name mysql-container --rm -p 3306:3306 -e MYSQL_ROOT_PASSWORD=wordpress -e MYSQL_USER=wordpress -e MYSQL_PASSWORD=wordpress -e MYSQL_DATABASE=wordpress -d mysql:5.7
```
- We exhibit Port 3306 which is the default port of use of MySQL so that WordPress can communicate with the database
- Then we also launch a container with WordPress already installed and the necessary tools configured (Apache and PHP)
```
docker container run --name wordpress-container --rm -e WORDPRESS_DB_HOST=172.17.0.1 -e WORDPRESS_DB_PASSWORD=wordpress -e WORDPRESS_DB_USER=wordpress -e WORDPRES_DB_NAME=wordpress -p 8080:80 -d wordpress
```
- We note that we give as an environment parameter a certain number of elements to our container to allow it to communicate with the container of the database, but also the exposure of the port necessary to display our application

## Creation of a network for us two containers

- The problem of the above solution is as follows: our database is exposed outside which poses security problems.In addition during the launch of the WordPress container we need to know the IP address of the MySQL container, outside if it changes, it will therefore also have to modify the parameters of our WordPress container.
- To avoid this, it is recommended to use a specific network, for this to create a network :
```
docker network create if_wordpress
```
- Then we recreate our two containers by attaching them to this network, which will allow our two containers to communicate with each otherr :
```
docker container run --name mysql-container --rm --network if_wordpress -e MYSQL_ROOT_PASSWORD=wordpress -e MYSQL_USER=wordpress -e MYSQL_PASSWORD=wordpress -e MYSQL_DATABASE=wordpress -d mysql:5.7
docker container run --name wordpress-container --rm --network if_wordpress e WORDPRESS_DB_HOST=172.17.0.1 -e WORDPRESS_DB_PASSWORD=wordpress -e WORDPRESS_DB_USER=wordpress -e WORDPRES_DB_NAME=wordpress  -p 8080:80 -d wordpress
```
- We can see that the DB_HOST of Wordress has become the name of our container and no longer its IP.Indeed the use of a dedicated network makes it possible to allow our containers to communicate with each other on any port and that simply using the name (or containerid) of the container with which he wishes to communicate

## Simplification with the use of Docker composes

- We will now simplify the use of our containers, by assembling our two containers in a Docker-Complete file which will allow you to pass all the parameters necessary for our containers, but also the creation of the dedicated network
- For that let's start by stopping and deleting our old containers
```
docker container stop mysql-container wordpress-container
docker system prune
```
- Then we will create our Docker-compose.yml file by adding the first container of MySQL
```
version: '3.1'

services:
 # Do not use Underscore in the name of the service, it generates errors when using the name as a host
  mysql-container:
    image: mysql:5.7
    ports:
      - 3306:3306
    environment:
      MYSQL_ROOT_PASSWORD: wordpress
```
- MySQL's container was added as a service
- To launch the file we use
```
docker compose up
```
- This will create as many containers as there are services in your file
- From the Run control of the WordPress container, add to the Docker composes a service for the WordPress container
- Once the service is added, use the following command again to check that your services work
```
docker compose up
```
- If you look at the network side, what do you see ?

-> Well done, you now know how to bring together containers in the form of a service to easily manage several containers for a single application.
