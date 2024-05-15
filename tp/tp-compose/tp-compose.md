# Une application multi-conteneur avec docker compose

Dans ce TP, nous allons conteneriser un site web qui utilise Wordpress, nous allons donc avoir deux conteneurs pour cela, un pour apache / php et un pour la base de données qui devront communiquer entre eux. Le site web devra être accessible de l'extérieur, nous auront donc également besoin de mapper des ports.
Pour cela nous allons utiliser  docker-compose qui permet de lancer en même temps plusieurs conteneurs.

## Lancer manuellement les 2 conteneurs 
- Pour démarrer nous allons lancer un nouveau conteneur mysql :
```
docker container run --name mysql-container --rm -p 3306:3306 -e MYSQL_ROOT_PASSWORD=wordpress -e MYSQL_DATABASE=exampledb -e MYSQL_USER=exampleuser -e MYSQL_PASSWORD=examplepass -d mysql:5.7
```
- Nous exposons le port 3306 qui est le port par défaut d'utilisation de mysql pour que Wordpress puisse communiquer avec la base de données
- Puis nous lançons également un conteneur avec wordpress déjà installé et les outils nécessaires configurés (apache et PHP)
```
docker container run --name wordpress-container --rm -e WORDPRESS_DB_HOST=172.17.0.1 -e WORDPRESS_DB_PASSWORD=wordpress -e WORDPRESS_DB_USER=exampleuser -e WORDPRESS_DB_NAME=exampledb -p 8080:80 -d wordpress
```
- On constate que l'on donne en paramètre d'environnement un certain nombre d'éléments à notre conteneur pour lui permettre de communiquer avec le conteneur de la base de données, mais aussi l'exposition du port nécessaire pour afficher notre application

## Création d'un réseau pour nous deux conteneurs 
- Le problème de la solution ci-dessus est le suivant : notre base de données est exposée à l'extérieur ce qui pose des problèmes de sécurité. De plus lors du lancement du conteneur de wordpress nous avons besoin de connaitre l'adresse IP du conteneur mysql, hors si celle-ci change, il va donc falloir modifier également les paramètres de notre conteneur wordpress.
- Pour éviter cela, il est recommandé d'utiliser un réseau spécifique, pour cela crééer un réseau :
```
docker network create if_wordpress
```
- Ensuite nous recréons nos deux conteneurs en les rattachant à ce réseau, ce qui permettra à nos deux conteneurs de communiquer entre eux :
```
docker container run --name mysql-container --rm --network if_wordpress -e MYSQL_ROOT_PASSWORD=wordpress -e MYSQL_DATABASE=exampledb -e MYSQL_USER=exampleuser -e MYSQL_PASSWORD=examplepass -d mysql:5.7
docker container run --name wordpress-container --rm --network if_wordpress -e WORDPRESS_DB_HOST=mysql-container -e WORDPRESS_DB_PASSWORD=examplepass -e WORDPRESS_DB_USER=exampleuser -e WORDPRESS_DB_NAME=exampledb -p 8080:80 -d wordpress
```
- On peut constater que le db_host de wordress est devenu le nom de notre conteneur et non plus son IP. En effet l'utilisation d'un réseau dédié permet d'autoriser à nos conteneurs de communiquer entre eux sur n'importe quel port et cela simplement en utilisant le nom (ou le containerID) du conteneur avec lequel il souhaite communiquer.

## Simplification avec l'utilisation de Docker compose
- Nous allons maintenant simplifier l'utilisation de nos conteneurs, en assemblant nos deux conteneurs dans un fichier docker-compose qui permettra de passer tous les paramètres nécessaires à nos conteneurs, mais aussi la création du réseau dédié.
- Pour cela commençons par arrêter et supprimer nos anciens conteneurs :
```
docker container stop mysql-container wordpress-container
docker system prune
```
- Puis nous allons créér notre fichier docker-compose.yml en ajoutant le premier conteneur de mysql :
```
version: '3.1'

services:
 # Ne pas utiliser d'underscore dans le nom du service, cela génère des erreurs lors de l'utilisation du nom en tant qu'hôte
  mysql-container:
    image: mysql
    ports:
      - 3306:3306
    environment:
      MYSQL_ROOT_PASSWORD: wordpress
```
- Le conteneur de mysql a été ajouté en tant que service
- POur lancer le fichier on utilise :
```
docker compose up
```
- Cela crééra autant de conteneurs qu'il y a de services dans votre fichier
- A partir de la commande de run du conteneur de wordpress, ajouter au docker compose un service pour le conteneur wordpress
- Une fois le service ajouter, utiliser de nouveau la commande suivante pour vérifier que vos services fonctionnes 
```
docker compose up
```
- Si vous regarder du côté des réseaux, que constatez vous ?

-> Bravo, vous savez maintenant comment rassemblé des conteneurs sous forme de service pour gérer facilement plusieurs conteneurs pour une seule application.
