# TP8 : Orchestrer ses conteneurs avec docher machine et swarm

Ce dernier TP va permettre de mettre en place un cluster avec Swarm et ses dockers machines mais aussi du load balancing avec Traefik.
Pour cela l'application Consul (https://github.com/WeScale/consul-spring-docker) écrite en Java avec Spring permettant d'exposer une API Rest sera utilisée comme application à déployer.

## Pré-requis : installation docker machine

- Pour installer docker machine, suivre les instructions de cette page :
https://docs.docker.com/machine/install-machine/

## Orchestrateur de conteneurs
- Commencer avec la création de 3 machines : un manager et deux workers :
```
docker-machine create \
      --engine-env 'DOCKER_OPTS="-H unix:///var/run/docker.sock"' \
      --driver virtualbox \
      leader1
      
docker-machine create \
      --engine-env 'DOCKER_OPTS="-H unix:///var/run/docker.sock"' \
      --driver virtualbox \
      worker1
      
docker-machine create \
      --engine-env 'DOCKER_OPTS="-H unix:///var/run/docker.sock"' \
      --driver virtualbox \
      worker2
```
- Une fois les machines en place, il est temps d'initialiser le cluster swarm :
```
ip_leader1=$(docker-machine ip leader1)

eval "$(docker-machine env leader1)"

docker swarm init \
    --listen-addr $ip_leader1 \
    --advertise-addr $ip_leader1

token=$(docker swarm join-token worker -q)

eval "$(docker-machine env worker1)"

docker swarm join \
    --token $token \
    $ip_leader1:2377

eval "$(docker-machine env worker2)"

docker swarm join \
    --token $token \
    $ip_leader1:2377
```
- Puis de créer un réseau dédié à notre cluster :
```
eval "$(docker-machine env leader1)"

docker network create \
    -d overlay --subnet 10.1.9.0/24 \
    multi-host-net
```
- Enfin, ajouter un service qui permet de visualiser le cluster :
```
eval "$(docker-machine env leader1)"

docker service create \
  --name=viz \
  --publish=5050:8080/tcp \
  --constraint=node.role==manager \
  --mount=type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock \
  manomarks/visualizer
```
- L'application de visualisation sur http://ip_machine:5050 

## Ajouter l'application rest au cluster
- Créer le premier service leader avec une contrainte sur l'execution sur le noeud leader1:
```
docker service create --replicas 1 \
    --name consul-leader \
    --publish 8501:8500 \
    --network multi-host-net \
    --constraint=node.hostname=='leader1' \
    progrium/consul -server -bootstrap-expect 1 -ui-dir /ui
```
- Puis créer un deuxième service en mode global pour monter le cluster
```
docker service create \
    --name consul-nodes \
    --publish 8500:8500 \
    --network multi-host-net \
    --mode global \
    progrium/consul -server -join $ip_consul_leader -ui-dir /ui
```
- L'application est prête et renvoit le nom de son instance : 
http://ip_machine:8500
- Il est aussi possible de visualiser les services dans le visualiseur qui a été mis en place à l'étape précédente

## Mise en place du load balancing
- Création d'un fichier de configuration trafik.toml avec le contenu suivant :
```
defaultEntryPoints = ["http"]

[entryPoints]
  [entryPoints.http]
  address = ":80"


[consul]
  watch = true
  prefix = "traefik"


[consulCatalog]
  domain = "localhost"
  prefix = "traefik-consul"


[web]
  address = ":8080"
```
- Puis le lancement du service traefik :
```
docker service create \
    --name traefik \
    --constraint=node.role==manager \
    --publish 80:80 \
    --publish 8080:8080 \
    --mount type=bind,source=$PWD/traefik.toml,target=/etc/traefik/traefik.toml \
    --network multi-host-net \
    --mode global \
    traefik \
    --consulCatalog.endpoint=consul-nodes.multi-host-net:8500 \
    --consul.endpoint=consul-nodes.multi-host-net:8500 \
    --web
```
- L'environnement est prêt avec notre cluster et notre load balancer

## Test de haute disponibilité

- Tester si l'application est bien load balancé :
```
curl -H Host:democonsul.localhost http://192.168.99.100
```
- Ajouter deux noeuds pour tester la scalabilité de notre cluster
```
docker-machine create \
      --engine-env 'DOCKER_OPTS="-H unix:///var/run/docker.sock"' \
      --driver virtualbox \
      leader2
      
docker-machine create \
      --engine-env 'DOCKER_OPTS="-H unix:///var/run/docker.sock"' \
      --driver virtualbox \
      worker3

eval "$(docker-machine env leader1)"

token_leader=$(docker swarm join-token manager -q)

token=$(docker swarm join-token worker -q)

eval "$(docker-machine env worker3)"

docker swarm join \
    --token $token \
    $ip_leader1:2377

eval "$(docker-machine env leader2)"

docker swarm join \
    --token $token_leader \
    $ip_leader1:2377
```
- Il est maintenant possible de scaler manuellement son application :
```
docker service scale web=10
```
- Ou de supprimer un noeud : Swarm répartira alors les containers sur les autres noeuds :
```
docker-machine rm worker3 --force
```
- Vérifier sur le visualiseur ce qu'il s'est passé ?

--> Bien joué, vous avez terminé l'ensemble des TP de la formation DOcker, voyons maintenant sur un exemple de projet sans guide si vous arrivez à mettre en pratique tout ce qu'on a vu :) 

