# TP 1 - Création de l'environnement de travail (VM) et installation de Docker

## Step 1 : installation de la VM 
* Télécharger VirtualBox : https://www.virtualbox.org/wiki/Downloads
* Une fois installé, créer une VM avec Ubuntu 20.04 dessus avec les caractéristiques suivantes :
* * 4Go de RAM
* * 10GO d'espace disque
* * 2 vcpu (ou plus en fonction de vos config machine)
* * partage du réseau avec la machine hôté


## Step 2 : Installer docker 
* Démarrer la VM
* Installer docker : [https://www.docker.com/get-started](https://docs.docker.com/engine/)

## Installation avec Chocolatey sur Windows

* Installer Chocolatey : https://chocolatey.org/install
* Une fois chocolatey installé, ouvrir un PowerShell et taper la commande `choco install docker-engine`


## Tester l'installation de docker 

* Une fois l'installation terminée, ouvrez un terminal et taper :
```
docker run hello-world
```
* Le retour devrait être :
```
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
0e03bdcc26d7: Pull complete
Digest: sha256:8e3114318a995a1ee497790535e7b88365222a21771ae7e53687ad76563e8e76
Status: Downloaded newer image for hello-world:latest

Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/
For more examples and ideas, visit:
 https://docs.docker.com/get-started/
```
 * -> Félicitations, votre docker fonctionne ! 

