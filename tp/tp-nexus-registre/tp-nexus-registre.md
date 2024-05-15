# Installer et configurer un repository Nexus en tant que registre privé


## Lancement du nexus :

* Créer un fichier docker compose avec le contenu suivant :
```
version: '3'
services:
  nexus:
    volumes:
      - nexus-data:/nexus-data
    #Avoid conflict with macAffee which using port 8081 and 8082
    ports:
      - "8099:8081"
      - "8082:8082"
      - "8083:8083"
    image: sonatype/nexus3
    container_name: nexus
volumes:
  nexus-data: {}
```
* Lancer le conteneur avec `docker compose up -d`

## Configurer nexus et se connecter depuis docker : 

https://medium.com/@yasinkartal2009/using-nexus-repository-manager-as-docker-images-50038bf5b097
* Pour la partie daemondocker voir ici pour les chemins : https://docs.docker.com/config/daemon/#configuration-file 
