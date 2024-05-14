# Manipuler les volumes

* Docker permet de manipuler les volumes qui sont liés à n'importe quel conteneur. Ces volumes sont déclarés à l'avance puis consommés, ou bien déclarés implicitement au démarrage du conteneur.

* Nous allons démarrer un conteneur nginx avec pour objectif de servir non pas des fichiers inclus dans l'images, mais des fichiers de l'hôte (votre poste de travail).

## Utiliser un volume de type Bind

* On prend un simple fichier html que l'on sauvegarde dans le dossier courant sous le nom index.html :

```
<html>
    <head>
        <title>Test page</title>
    </head>
    <body>
        <p>Ceci est une page de test</p>
    </body>
</html>
```
* Et l'objectif va être de le monter dans le dossier de nginx pour qu'il le serve :

```
docker run -d -v .:/usr/share/nginx/html -p 8098:80 nginx
docker: Error response from daemon: create .: volume name is too short, names should be at least two alphanumeric characters.
See 'docker run --help'.
```

* Pourquoi ne peut-on pas lier le dossier courant ?

-> Docker attend un chemin d'au moins 2 caractère par le cli, il faut alors user d'une petite ruse pour monter le volume :

* Sous linux :

```
$ docker run -d -v $(pwd):/usr/share/nginx/html -p 8098:80 nginx
458902306f687604d8a91f4df7269206d582bd383f7ec1866c0b757188bd2e53
```

* Sous Powershell :

```
> docker run -d -v ${PWD}:/usr/share/nginx/html -p 8098:80 nginx
458902306f687604d8a91f4df7269206d582bd383f7ec1866c0b757188bd2e53
```

* Sous CMD :

```
> docker run -d -v %cd%:/usr/share/nginx/html -p 8098:80 nginx
458902306f687604d8a91f4df7269206d582bd383f7ec1866c0b757188bd2e53
```

* Si on se rend maintenant sur la page localhost:8098, on verra bien notre index.html

* Modifier le fichier .html dans le répertoire du poste de travail, raffraichir la page. Celle-ci doit avoir changé en conséquence.


## Utiliser un volume de type Volume

* L'opération que nous venons de réaliser consiste à créer implicitement un volume de type Bind et à l'attacher au conteneur.
* Les volumes Bind sont pratiques en phase de développement mais leur utilisation n'est pas recommandée en production. Dans ce contexte on préfèrera utiliser un volume géré par docker.
* Commençons par inspecter notre conteneur précédent pour constater le type de montage que nous avons réalisé

```
docker inspect <id du conteneur>
```

* Chercher la section Mounts, remarquer les valeurs des attributs Type et Source

* Nous allons maintenant créer un volume géré par docker

```
docker volume create -d local <choisir un nom de volume>
```

* L'argument -d nous permet ici d'indiquer que nous allons utiliser le driver local. Celui-ci stocke les données dans un répertoire local sur l'hôt. Il éxiste de nombreux autres drivers de volume (cf https://docs.docker.com/engine/extend/legacy_plugins/#volume-plugins)
* Controller la bonne création du volume

 ```
docker volume ls
```
* Nous pouvons également afficher des détails sur le volume. Ces détails seront spécifique au driver utilisé, dans le cas du driver local, on va pouvoir découvrir l'emplacement réel des fichiers du volume

```
docker volume inspect <nom du volume>
```
* Il est temps de relier notre volume à un conteneur avec docker run

```
docker run -d -v <nom du volume>:/usr/share/nginx/html -p 8098:80 nginx
```
* Accéder à la page http://localhost:8098 depuis un navigateur. La page par défaut d'nginx doit s'afficher.

* Réaliser les opérations suivantes :
  * Utiliser docker cp pour remplacer cette page par défaut par une autre
  * Arrêter et supprimer le conteneur
  * Recréer un conteneur en montant le même volume

* Quelle page s'affiche désormais ?

## Comprendre l'instruction VOLUME de Dockerfile

* Réaliser les opérations suivantes :
  * Supprimer le conteneur précédent
  * Créer un nouveau volume
  * Créer un conteneur basé sur l'image que nous avons préparée au TP précédent, monter le nouveau volume dans /var/www/html
  * Accéder au serveur depuis un navigateur, quel est le résultat ?
  * Supprimer le conteneur et son volume (docker volume rm <nom du volume)
  * Modifier le Dockerfile en ajoutant l'instruction VOLUME /var/www/html, reconstruire l'image
  * Recréer un volume et recréer un conteneur sur la nouvelle version de l'image
  * Accéder au serveur depuis un navigateur

