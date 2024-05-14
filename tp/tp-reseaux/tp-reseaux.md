
# TP - Réseaux docker

* Docker permet de manipuler l'accès au réseau des conteneurs, de manière implicite en déclarant un mapping de port sur l'hôte au moment de démarrer un conteneur avec docker run, ou de manière plus controllée en préconfigurant des réseaux gérés par docker.

## Manipuler les ports avec docker run

* Analysons un peu plus en détails une commande que nous avons déjà exécutée

```
$ docker run -p 8098:80 nginx
```

* Le paramètre -p (--publish), publie les ports selon les paramètres donnés. Ici on indique que le port local 8098 est mappé sur le port 80 du conteneur.


* Accédez à : http://localhost:8098/

* On a lancé un container sur la base d'une image nginx. L'image nginx est configurée pour écouter sur le port 80, et on redirige le port de 8098 de l'hôte vers le port 80 du container.

* Le listing des containers nous indique également les ports qui sont publiés :

```
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                  NAMES
074c3ec99282        nginx               "nginx -g 'daemon of…"   2 seconds ago       Up 1 second         0.0.0.0:8098->80/tcp   cranky_kapitsa
```

* Si on souhaite publier plusieurs port, il suffit de mettre plusieurs fois le paramètre -p:

```
$ docker run -d -p 8098:80 -p 8099:443 nginx
```

* Ici on redirige les ports 8098 et 8099 de l'hôte vers les ports 80 (http) et 443 (https) du conteneur.

* Que se passe-t-il si on essaie de publier le même port sur deux containers ?

```
$ docker run -p 8098:80 httpd 
```

* Une fois un port attaché à l'hôte, le port local (8098 dans l'exemple précédent) ne peut plus être réutilisé.

* Il existe un raccourci permettant d'écouter sur tous les ports exposés du conteneur

```
docker run -d -P nginx
```
* L'option -P (--publish-all) expose un port de l'hôte choisi aléatoirement pour chaque port exposé par le conteneur. Les ports exposés sont ceux listés derrière une directive EXPOSE dans le Dockerfile. Attention, la directive EXPOSE n'est que déclarative, rien ne garanti qu'un service écoute effectivement derrière ce port.

## Utiliser les réseaux docker

* À titre d'exercice nous allons créer deux micro-services en php.
  * time-ws : ce microservice répond aux requêtes GET / avec le timestamp système actuel
  * tomorrow-ws : ce microservice se connecte à time-ws pour récupérer un timestamp T, et répond aux requêtes GET / avec la date T + 1 jour sous la forme jj/mm/AAAA.

### time-ws

* Commençons par écrire time-ws dans un fichier time-ws.php

```
<?php
printf(time());
```

* Testons ce service localement. Peut-être n'avez-vous pas PHP installé sur votre poste, nous allons donc utiliser Docker pour exécuter php en ligne de commande.

```
docker run -it --rm --name test-ws -v ${PWD}:/usr/src/test-ws -w /usr/src/test-ws php:7.2-cli php time-ws.php
```

* On doit voir un timestamp unix s'afficher.

* Nous allons créer une image docker contenant ce web-service en nous appuyant sur l'image officielle php, dans sa variante apache (cf. https://hub.docker.com/_/php/). La variante apache nous permet de conserver un script simple et de déléguer la gestion des requêtes HTTP à apache.

* Créer un fichier time-ws.dockerfile

```
FROM php:7.2-apache

COPY time-ws.php /var/www/html/index.php
```
* Construire l'image en utilisant le repository time-ws (à vous d'indiquer les bons paramètres !).
```
docker build ...
```
* Nous allons pouvoir tester notre web-service en exécutant un conteneur démonisé auquel nous allons attribuer un mapping de port (et un nom pour pouvoir le manipuler plus facilement)

```
docker run -p 8083:80 -d --name time-ws time-ws
```
* Tester localement en accédant à http://localhost:8083 depuis un navigateur. Si tout fonctionne bien, un timestamp doit s'afficher dans la fenêtre du navigateur.

### tomorrow-ws

* Vous pouvez maintenant reproduire les même étapes pour créer tomorrow-ws dont voici le code

tomorrow-ws.php
```
<?php
$c = curl_init('http://localhost:8083');
curl_setopt($c, CURLOPT_RETURNTRANSFER, 1);
$res = curl_exec($c);
printf(date("d/m/Y", $res+3600*24));
```
* Noter l'initialisation suivante : curl_init('http://localhost:8083');

* Ici nous avons indiqué localhost comme adresse de serveur, cela va-il fonctionner ? Tout dépend du contexte réseau !
* Reprenons le docker run de tout à l'heure pour lancer le script en ligne de commande (seul le nom du script change, à la fin de la commande)
```
docker run -it --rm --name test-ws -v ${PWD}:/usr/src/test-ws -w /usr/src/test-ws php:7.2-cli php tomorrow-ws.php

$ docker run ... 
02/01/1970
```
* Le résultat qui s'affiche sur la sortie standard est complètement faux ! Nous avons en effet ajouté une journée, mais en partant du 01/01/1970 au lieu de la date actuelle. Autrement dit l'appel réseau a échoué et nous n'avons pas obtenu de timestamp.

* Nous allons ajouter l'option --net host à notre commande pour remédier à ça
```
docker run -it --rm --name test-ws \
           -v ${PWD}:/usr/src/test-ws \
           -w /usr/src/test-ws \
           --net host  \
           php:7.2-cli php tomorrow-ws.php
```
* La date qui s'affiche est bien la date attendue.
* Que s'est-il passé ?

* Avant de passer à la suite, nous allons lancer notre tomorow-ws en mode démonisé
```
docker run -p 8082:80 -d --name tomorrow-ws tomorrow-ws
```

## Communication inter-conteneurs

* Dans l'état actuel des choses, nous devrions avoir les éléments suivants :
  * time-ws est lancé dans un conteneur en mode démonisé, accessible sur le réseau de l'hôte par le port 8083
  * tomorrow-ws est lancé de la même manière, accessible sur le port 8082

* Dans cette configuration, tomorrow-ws ne peut pas contacter time-ws car il essaye pour l'instant de contacter localhost. On peut le confirmer en accédant à http://localhost:8082 depuis un navigateur, la date indiquée est le 02/01/1970.
* Nous pourrions lancer tomorrow-ws avec l'option --net host, mais cette pratique est déconseillée car trop permissive.
* De plus, cette architecture est imparfaite car elle ne nous permet pas de contrôler la visibilité réseau des différents services. Nous pourrions en effet souhaiter rendre tomorrow accessible publiquement, tandis que time-ws n'est accessible que pour tomorrow-ws.
* Pour toutes ces raisons, nous allons modifier le mode d'accès au réseau de nos conteneurs pour utiliser des réseaux gérés par docker.
* Commençons par inspecter un de nos conteneurs pour vérifier sur quel réseau il se trouve
```
docker inspect tomorrow-ws
```
* La section Networks nous permet de constater que notre conteneur est sur le réseau bridge par défaut, et nous pouvons afficher quelques détails sur ce réseau.
```
docker network ls
docker network inspect bridge
```
* Notre objectif est de créer un nouveau réseau docker de type bridge, entièrement dédié à nos deux micro-services.

* L'opération est très simple :
```
docker network create -d bridge time-network
```
* Nous pouvons maintenant détruire nos conteneurs et les recréer sur leur réseau dédié. Pour l'instant, nous n'allons pas leur réattribuer de port.
```
docker stop time-ws tomorrow-ws
docker rm time-ws tomorrow-ws
docker run --net time-network -d --name time-ws time-ws
docker run --net time-network -d --name tomorrow-ws tomorrow-ws
```
* Comment tomorrow-ws va pouvoir contacter time-ws désormais ?

* Deux solutions s'offrent à nous : - utiliser l'IP du conteneur - utiliser son nom DNS

* Nous allons tester manuellement les deux. Pour commencer, il nous faut l'IP du conteneur time-ws
```
docker inspect time-ws
```
* À la section Networks on trouver l'information qui nous intéresse :
```
"Networks": {
    "time-network": {
        "IPAMConfig": null,
        "Links": null,
        "Aliases": [
            "5f9832dc2db7"
        ],
        "NetworkID": "ae521b40dcaae023b4b9f52bc501b423224031b5a64a4b91681316b614a426a3",
        "EndpointID": "87886285e4da9da5e47ed14b890ad440dff49fa56d8e6d74601fede97d16c383",
        "Gateway": "172.21.0.1",
        "IPAddress": "172.21.0.2",
        "IPPrefixLen": 16,
        "IPv6Gateway": "",
        "GlobalIPv6Address": "",
        "GlobalIPv6PrefixLen": 0,
        "MacAddress": "02:42:ac:15:00:02",
        "DriverOpts": null
    }
}
```
* Pour tester, nous allons nous connecter "à l'intérieur" de tomorrow-ws
```
docker exec -it tomorrow-ws /bin/bash
```
* De là, il est simple de vérifier la connexion avec curl (on doit voir un timestamp s'afficher)
```
curl 172.21.0.2
```
* Utiliser l'adresse IP du conteneur n'est pas une solution viable. Celle-ci est susceptible de changer si le conteneur venait à être recréé. Notre réseau docker offre une solution à cette problématique grâce à la résolution DNS par nom de conteneur. Il est en effet possible d'adresser les conteneurs d'un même réseau par leur nom directement, ce qui permet par exemple d'exécuter cette commande avec succès :
```
curl time-ws
```
* Nous pourrions en rester là et remplacer localhost par time-ws dans le code de tomorrow-ws, mais nous allons prendre un peu plus de temps pour faire le choses proprement et rendre cette adresse configurable.

* Dans le monde de Docker et du cloud, qui dit paramètre dit généralement variable d'environnement. C'est ce que nous allons utiliser, modifions tomorrow-ws.php en conséquence.

```
<?php
$host = getenv('TIME_WS_HOSTNAME');
$port = getenv('TIME_WS_PORT');
$c = curl_init( sprintf('http://%s:%s', $host, $port));
curl_setopt($c, CURLOPT_RETURNTRANSFER, 1);
$res = curl_exec($c);
printf(date("d/m/Y", $res+3600*24));
```
* Reconstruire l'image
```
docker build -t tomorrow-ws -f tomorrow.dockerfile .
```
* Supprimer le conteneur tomorrow-ws en cours d'exécution
```
docker stop tomorrow-ws
docker rm tomorrow-ws
```
* Enfin, nous allons relancer le conteneur en déclarant les variables d'environnement adéquates et en affectant un mapping de port pour pouvoir joindre le conteneur depuis l'hôte.
```
docker run --net time-network -d --name tomorrow-ws \
           -e TIME_WS_HOSTNAME=time-ws \
           -e TIME_WS_PORT=80 \
           -p 8082:80 \
           tomorrow-ws
```
* Accéder à http://localhost:8082, on doit bien voir la date du lendemain s'afficher !

* Pour bien finaliser les choses, nous allons déclarer les variables d'environnement dans le dockerfiel de tomorrow-ws. Cela nous permettra de documenter leur existence ainsi que de leur donner un valeur par défaut.
```Manipuler les ports avec docker run
FROM php:7.2-apache

ENV TIME_WS_HOSTNAME time-ws
ENV TIME_WS_PORT 80

COPY tomorrow-ws.php /var/www/html/index.php
```
* En reconstruisant l'image, on pourrait ainsi lancer le conteneur en omettant les options -e.
