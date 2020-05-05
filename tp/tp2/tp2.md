# TP 2: Gérer nos premiers conteneurs en ligne de commande

## Récupérer un conteneur depuis Docker hub
- Récupérer depuis le docker hub le conteneur alpine:
```
docker image pull alpine
```
- Lister les images pour vérifier que l'image a bien été téléchargée :
```
docker image ls
```
- Lancer le conteneur alpine avec la commande ls pour voir ce qu'il contient :
```
docker container run alpine ls -l
```
## Instance de conteneurs
- Afficher un message "Bienvenue depuis alpine" au lancement du conteneur :
```
docker container run alpine echo "Bienvenue depuis alpine"
```
- Lancer un terminal dans notre conteneur :
```
docker container run alpine /bin/sh
```
- Lancer un conteneur en mode interractif :
```
docker container run -it alpine /bin/sh
```
- Lister les conteneurs :
```
docker container ls -a
```
- Combien de conteneurs sont présents ?

## Isolation des conteneurs :
- Ajoutons un nouveau conteneur basé sur alpine en appelant cette fois le shell ash :
```
docker container run -it alpine /bin/ash
```
- Vous pouvez maintenant taper des commandes dans votre conteneur:
```
echo "bienvenue" > hello.txt
ls
```
- Quels sont les fichiers qui apparaissent ?

- Maintenant essayons une fois sorti du terminal du conteneur (exit), d'afficher les fichiers du conteneur :
```
docker conteneur run alpine ls
```
- Que constatez vous ?
- -> Il s'agit de l'isolation de docker entre la machine hote et les conteneurs, les fichiers ne sont pas accessible de l'exterieur

- Lançons de nouveau notre contenur :
```
docker container ls -a
docker container start <containerID>
```
- Astuce : vous pouvez utilisez seulements les premiers caractères de l'id pour le containerID
- Maintenant que le conteneur est démarré nous pouvons executer à l'intérieur la commande ls avec exec :
```
docker container exec <containerID> ls
```
- Notre fichier hello.txt apparait bien!

## Nettoyage des containers
- Ce premier tp étant terminé, nous allons nettoyer nos instances de container :
```
docker system prune
```