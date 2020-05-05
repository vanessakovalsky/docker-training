# Corrigé TP 1 - Création de l'environnement de travail (VM) et installation de Docker

## Step 1 : installation de la VM 
### Installation de VirtualBox
- Télécharger VirtualBox : https://www.virtualbox.org/wiki/Downloads
- Suivez les étapes d'installation :
- La première étape vous informe, cliquer sur Installer
![install_vb1](https://github.com/vanessakovalsky/docker-training/blob/master/tp/tp1/corrige/images/install_vb1.PNG)
- La seconde étape vous invite à choisir les outils à installer : laisser les options par défaut
![install_vb2](https://github.com/vanessakovalsky/docker-training/blob/master/tp/tp1/corrige/images/install_vb2.PNG)
- La troisième étape vous permet de créer des raccourcis pour accéder à VirtualBox
![install_vb3](https://github.com/vanessakovalsky/docker-training/blob/master/tp/tp1/corrige/images/install_vb3.PNG)
- La quatrième étape vous avertit que l'installation va temporairement déconnecter votre réseau
![install_vb4](https://github.com/vanessakovalsky/docker-training/blob/master/tp/tp1/corrige/images/install_vb4.PNG)
- La cinquième étape vous informe que l'installation est prête : cliquer sur Installer
![install_vb5](https://github.com/vanessakovalsky/docker-training/blob/master/tp/tp1/corrige/images/install_vb5.PNG)
- L'étape suivante installe le logiciel (attendre la fin)
![install_vb6](https://github.com/vanessakovalsky/docker-training/blob/master/tp/tp1/corrige/images/install_vb6.PNG)
- L'outil est installé, il propose de démarrer
![install_vb7](https://github.com/vanessakovalsky/docker-training/blob/master/tp/tp1/corrige/images/install_vb7.PNG)

### Création de la VM

- Une fois installé, créer une VM avec Ubuntu 20.04 dessus avec les caractéristiques suivantes :



## Step 2 : Installer docker 
- Démarrer la VM
- Installer docker : https://www.docker.com/get-started
- Une fois l'installation terminée, ouvrez un terminal et taper :
docker run hello-world
- Le retour devrait être :
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
 - Félicitations, votre docker fonctionne ! 