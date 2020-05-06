# TP6 : Construire son propre registre et associer une interface d'administration à ses conteneurs

Ce TP nous permet d'installer au sein d'un docker notre propre registre privé pour gérer nos images, mais aussi de le sécuriser en lui ajoutant un certifat SSL et un mécanisme basique d'authentification ainsi qu'une interface graphique

## Installer notre registre privé
- Créer un fichier docker-compose.yml
- Déclarer un service pour notre registry qui s'appuie sur l'image : registry:2
- Ajouter en variable d'environnement à notre service :
```
REGISTRY_STORAGE_FILESYSTEM_ROOTDIRECTORY: /data
```
- Ajouter également un volume, monter dans le conteneur sur /data (ou tout autre chemin utiliser dans la variable d'environnement)
- Le registre privé doit alors être accessible sur URL-DE-VOTRE-HOST:5000 (si vous etes sur le labs pensez à ouvrir le port 5000)

## Sécuriser notre registre privé 
- Pour commencer, créer des certificats SSL (ceux-ci sont auto-générés ils générent un message d'avertissement dans le navigateur, vous pouvez aussi utiliser Let's Encrypt pour obtenir des certificats reconnus par les navigateurs). Manip à faire sur la machine hôte)
```
mkdir certs
openssl req \
    -newkey rsa:4096 -nodes -sha256 -keyout certs/localhost.key \
    -x509 -days 365 -out certs/localhost.crt
```
- Ajouter maintenant les options suivantes au service du docker compose (il s'agit des options utilisées avec un docker run à vous de les transformer en syntaxe pour docker-compose)
 ```
     -v "$(pwd)"/certs:/certs \         
    -e REGISTRY_HTTP_ADDR=0.0.0.0:443 \
    -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/localhost.crt \
    -e REGISTRY_HTTP_TLS_KEY=/certs/localhost.key \
    -p 443:443 \
```
- Ne pas oublier d'ajouter le volume sur le dossier contenant les certificats
- Relancer l'application
```
docker-compose stop
docker-compose down
docker-compose up
```
- Il est maintenant possible d'accéder à l'API de manière sécurisée pour lister les images (une fois le message d'avertissement du navigateur accepté)
URL-DE-VOTRE-HOTE/v2/_catalog

## Restreindre l'accès au registre privé

- Il est nécessaire d'ajouter une authentification, pour cela utiliser htpasswd (création d'un dossier puis génération depuis notre conteneur du fichier htpasswd)
```
mkdir auth
docker run --rm \
    --entrypoint htpasswd \
    registry:2 -Bbn testuser testpassword > auth/htpasswd
```
- Le fichier étant généré, il reste à l'utiliser dans notre docker-compose pour restreindre l'accès
- Ajouter au service du docker compose les informations suivantes (venant encore de la commande docker run donc à adapter)
```
-v "$(pwd)"/data:/var/lib/registry \
    -v "$(pwd)"/auth:/auth \
    -e "REGISTRY_AUTH=htpasswd" \
    -e "REGISTRY_AUTH_HTPASSWD_REALM=Registry Realm" \
    -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
```
- Penser à redémarrer l'application du docker compose
- Le registre est maintenant sécuriser

## Déposer ses images dans son registre privé
- Commencer par se connecter 
```
docker login URL-DE-VOTRE-HOST:5000

```
- Puis une fois le username et le password saisi, il est possible de push ses propres images :
```
docker push URL-DE-VOTRE-HOST:5000/newimage
```
- Le registre privé est prêt à être utiliser

## Ajouter l'interface graphique
- A partir de la commande suivante, ajouter un service au docker-compose qui va également lancer l'interface web pour le registre privé :
```
docker run -d --net registry-ui-net -p 80:80 -e REGISTRY_URL=http://registry-srv:5000 -e DELETE_IMAGES=true -e REGISTRY_TITLE="My registry" joxit/docker-registry-ui:static
```
- Penser à inclure une dépendance dans votre docker-compose pour que ce service ne se lance que si le registre privé fonctionne
- Penser également à ajouter l'option NGINX_PROXY_HEADER pour envoyer l'entête suivante avec les identifiants à votre registre privé (il peut être utile d'aller voir sur la page du projet pour avoir plus d'information : https://github.com/Joxit/docker-registry-ui)
```
http:
  headers:
    Access-Control-Allow-Origin: ['<your docker-registry-ui url>']
    Access-Control-Allow-Credentials: [true]
    Access-Control-Allow-Methods: ['HEAD', 'GET', 'OPTIONS'] # Optional
```