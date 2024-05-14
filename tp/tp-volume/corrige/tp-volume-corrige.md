# Corriger pour la dernière partie :

* Supprimer le conteneur précédent `docker stop <idduconteneur> && docker rm <idduconteneur>`
* Créer un nouveau volume `docker volume create nouveauvolume`
* Créer un conteneur basé sur l'image que nous avons préparée au TP précédent, monter le nouveau volume dans /var/www/html : `docker run -d -p 8888:80 -v nouveauvolume:/var/www/html monimage`
* Accéder au serveur depuis un navigateur, quel est le résultat ? -> page vide
* Supprimer le conteneur et son volume `docker stop <idduconteneur> && docker rm <idduconteneur> && docker volume rm <nom du volume>`
* Modifier le Dockerfile en ajoutant l'instruction VOLUME /var/www/html, reconstruire l'image : `docker build -t monimage:v3 .`
* Recréer un volume et recréer un conteneur sur la nouvelle version de l'image : `docker volume create nouveauvolume2 && docker run -d -p 8888:80 -v nouveauvolume2:/var/www/html monimage:v3`
* Accéder au serveur depuis un navigateur : on accède à la page d'index
