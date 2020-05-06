# Construire un conteneur personnalisé 

## Pré-requis :
- Récupérer le code dans ce depot (app.py et requirements.txt):
https://github.com/praqma-training/docker-katas/tree/master/labs/building-an-image

## Créer le docker file
- Nous allons créer un docker file pour pouvoir construire l'image nécessaire à l'execution de l'application :
- Créer un fichier Dockerfile (sans extension) au même niveau que les deux fichiers récupérer sur le dépôt
- Ouvrir le fichier (toutes les instructions seront à rajouter dans le fichier) et ajouter l'image de base :
```
FROM ubuntu:latest
```
- Ajouter maintenant l'installation des outils nécessaires :
```
RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential
```
- Ensuite installer les bibliothèques nécessaires à l'aide pip et du fichier requirements.txt :
```
COPY requirements.txt /usr/src/app/
RUN pip3 install --no-cache-dir -r /usr/src/app/requirements.txt
```
- Puis copier le fichier de l'application
```
COPY app.py /usr/src/app/
```
- Et exposer le port 5000 sur lequel l'application tourne 
```
EXPOSE 5000
```
- Enfin nous utilisons CMD pour lancer l'application
```
CMD ["python3", "/usr/src/app/app.py"]
```
- Notre dockerfile est prêt pour la suite

## Construction de notre image
- Dans le dossier avec le dockerfile, lancer la commande de build pour construire l'image :
```
docker build -t myfirstapp .
```
- Que s'est t'il passé pendant le build ?
- Vérifier que l'image est bien disponible :
```
docker images
```

## Lancement du conteneur avec l'image construite
- Il ne reste plus qu'à lancer le conteneur :
```
docker container run -p 8888:5000 --name myfirstapp myfirstapp
```
- Pour accéder à l'application, ouvrir le port 8888 sur l'hôte puisque c'est ce port qui est mappé sur le port 5000 de notre application (ou tout autre port au choix lors du lancement du conteneur)

## Layer des images :
- Chaque image construire est basée sur plusieurs layers, c'est-à-dire plusieurs images superposées les unes aux autres
- Pour voir l'ensemble des images utilisées par une image :
```
docker image history <image ID>
```
- Il est possible d'utiliser chacune de ces couches puisqu'elles sont mises en cache dans le gestionnaires d'images de docker, ce qui permet de réutiliser différents layers pour des images finales différentes

-> Bien joué, ce TP est terminé, vous pouvez maintenant essayer de créer des conteneurs personnalisé pour n'importe quelle application