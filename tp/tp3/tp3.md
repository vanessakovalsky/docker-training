# TP 3 - Créer un conteneur de BDD avec un volume et un conteneur web avec l'exposition d'un port

## Pré-requis

- Cloner le dépôt sur votre machine :     
git clone https://github.com/dockersamples/linux_tweet_app
- Créer un identifiant sur le hub docker :
https://hub.docker.com/ 

## Lancement de conteneur ubuntu et mysql
- Pour commencer on lance un conteneur ubuntu en mode interactif et on lui demande de lancer le processus bash :
```
 docker container run --interactive --tty --rm ubuntu bash
```
- Vous avez alors accès au terminal du conteneur ubuntu :
```
root@<container id>:/#
```
- On peut alors lancer des commandes linux standard :
```
ls
ps aux
cat /etc/issue
```
- Pour sortir du bash du conteneur : 
```
exit
```
- Passons maintenant au conteneur mysql
```
 docker container run -i \
 --detach \
 --name mydb \
 -e MYSQL_ROOT_PASSWORD=my-secret-pw \
 mysql:latest
 ```
 - On utilise le mode detach pour faire tourner le conteneur en fond, on lui donne un nom et on lui passe en paramètre d'environnement le mot de passe root de mysql que l'on souhaite définir, puis on utilise l'image mysql:latest
 - On vérifie que le conteneur s'est bien lancé en mode détaché :
```
  docker container ls
```
- Pour accéder au log du conteneur et savoir ce qu'il se passe :
```
docker container logs mydb
```
- Pour voir les process en cours dans notre conteneur :
```
docker container top mydb
```
- Pour obtenir la version de mysql utilisé dans notre container :
```
docker exec -it mydb \
 mysql --user=root --password=$MYSQL_ROOT_PASSWORD --version
```
- On va ensuite créer une base en passant en commande dans le conteneur mydb
```
 docker exec -it mydb sh
```
- Puis une fois dans le terminal on créé notre base
```
 mysql --user=root --password=$MYSQL_ROOT_PASSWORD 
```
 - Une fois dans le terminal de mysql : 
```
 CREATE DATABASE mydb;
 exit 
```
- On sort de notre conteneur :
```
 exit 
```

## Créer le volume et l'attacher à notre conteneur
- Créer le volume
```
docker volume create --name myvolume
```
- Enregistre l'image de notre conteneur mysql et la commiter  
```
docker commit <containerID> newimagename
```
- Relancer un conteneur en attachant notre volume à notre conteneur
```
docker run -ti -v myvolume:/chemin/vers/mysqldata newimagename /bin/bash
```
## Exposer le port 80 sur notre conteneur
- Installer apache sur notre conteneur Ubuntu :
```
docker container exec -t -i <containerID> '/bin/bash'
root@<containerID>:$ apt update && apt install apache2
```
- Enregistre l'image de notre conteneur mysql et la commiter  
```
docker commit <containerID> newimagename2
```
- Exposer le port 80
```
docker container run -i --detach -p 80:80 newimagename2
```

## Créer un montage avec le dossier partagé :
- On va maintenant monter le dossier dans lequel on a récupérer le depot github sur notre conteneur (se placer d'abord dans le dossier ou est le code du depot) :
```
docker run -d -it --name devtest --mount type=bind,source="$(pwd)"
 target=/chemin-vers-le-dossier-de-stockage  newimagename2
```
- Sur le labs : penser à ouvrir le port 80 dans l'interface
- Se rendre à l'url de votre labs : vous devriez voir votre page s'afficher

## Modifier un fichier
- Sur votre machine hote, modifier le fichier index.html
- Recharger votre page web avec l'url de votre lab : vos modifications devraient apparaître

## Pusher vos images :
- Se connecter au docker hub en commande :
```
docker login --username=yourhubusername --email=youremail@company.com
```
- Tagguer votre image :
```
docker tag <containerId> yourhubusername/newimagename2:firsttry
```
- Pusher votre images sur le dépôt :
```
docker push yourhubusername/newimagename2
```

-> Bien joué vous avez terminé ce TP 
