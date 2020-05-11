# TP7 : Administrer les conteneurs en centralisant les logs et en mettant en place du monitoring

Ce TP vise à mettre en place une réponse à deux besoin : centraliser et analyser les logs d'une part et monitorer nos conteneurs docker d'autre part.
Nous allons utiliser la stack ELK pour le premier besoin, et une suite composée de cAdvisor, Promotheus et Grafana pour le besoin de monitoring.

## Centralisation des logs

### MIse en place d'une application ELK
- On récupère le code ici : https://github.com/deviantony/docker-elk.git (git clone https://github.com/deviantony/docker-elk.git)
- On utilise le docker-compose.yml fournit à la racine
- Il ne reste plus qu'à le lancer avec un docker-compose up
- Une fois le démarrage terminé, vérifier en vous rendant sur :
http://ip_machine:9200/status qui affiche elastic search
- Kibana est accessible à l'adresse : http://ip_machine:5601  mais pour l'instant sans donnée il ne s'affiche pas
- L'environnement est prêt, il faut maintenant l'alimenter en données

### Envoyer des données à ELK
- Pour alimenter ELK en données, on utilise Filebeats qui va aller automatiquement lire les logs générées par docker, et les envoyer à logstash
- Pour cela ajouter au docker compose le service filebeat :
```
  filebeat:
    image: docker.elastic.co/beats/filebeat:7.6.2
    command: filebeat -e -strict.perms=false
    #volumnes mount depend on you OS ( Windows or Linux )
    volumes:
      - ./../docker-elk-filebeat/filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - ./../docker-elk-filebeat/filebeat/sample_log:/usr/share/filebeat/logs
    networks:
      - elk
    links:
       - elasticsearch
       - kibana
```
- Puis créer un dossier filebeat et un fichier filebeat.yml a l'interieur de ce dossier qui contient :
```
filebeat.config:
  modules:
    path: ${path.config}/modules.d/*.yml
    reload.enabled: false

filebeat.autodiscover:
  providers:
    - type: docker
      hints.enabled: true

processors:
- add_cloud_metadata: ~

output.elasticsearch:
  hosts: ["http://localhost:9200"]
  username: elastic
  password: changeme
```
- Pour vérifier que cela fonctionne, retourner sur la page de kibana, et valider le formulaire de création d'index (cela indique que Kibana a bien reçu des données)
- Cherchez dans l'interface de kibana ou sont afficher les logs de notre conteneur ?
- Relancer le docker-compose du tp 5 et et aller vérifier que les logs apparaissent bien dans kibana


## Mise en place du monitoring
### Ajouter un agent de supervision sur notre application
- Repartir du docker compose du tp 5 contenant notre application, et lui ajouter un agent de supervision cAdvisor

- Créons un nouveau docker-compose.yml pour ajouter un service cadvisor, qui sera chargé de récupérer les métriques des conteneurs :
```
  cadvisor:
    image: google/cadvisor
    container_name: cadvisor
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:rw
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    expose:
      - 8080
    ports:
      - "8005:8080"
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge
```
- Penser à rajouter le network monitoring sur les autres conteneurs
- Démarrer le conteneur (docker-compose up)
- En allant sur : http://ip_machine:8005 vous pourrez visualiser les métriques de vos conteneurs

### Ajout de promotheus pour rendre configurable notre supervision
- Pour aller plus loin et rendre cela configuration, ajouter Promotheus au docker-compose :
```
prometheus:
      image: prom/prometheus:latest
      container_name: prometheus
      volumes:
        - ./docker/prometheus/:/etc/prometheus/
        - prometheus-data:/prometheus
      command:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus'
        - '--web.console.libraries=/etc/prometheus/console_libraries'
        - '--web.console.templates=/etc/prometheus/consoles'
        - '--storage.tsdb.retention=200h'
      expose:
        - 9090
      ports:
        - "9090:9090"
      networks:
        - monitoring

volumes:
...
  prometheus-data: {}
```
- Créer un dossier /prometheus et à l'intérieur de ce dossier un fichier prometheus.yml (qui sert pour la configuration) avec le contenu suivant :
```
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'docker-host-alpha'

rule_files:
  - "targets.rules"
  - "host.rules"
  - "containers.rules"

scrape_configs:
  - job_name: 'cadvisor'
    scrape_interval: 5s
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'prometheus'
    scrape_interval: 10s
    static_configs:
      - targets: ['localhost:9090']
```
- Relancer un down un up sur le docker-compose
- Promotheus est accessible sur : http://ip_machine:9090/targets
- On peut alors vérifier le statut de nos conteneurs

### Ajouter des dashboard avec Grafana

- Ajouter alors l'interface pour créer et visualiser des dashboard grafana au docker compose :
```
 grafana:
    image: grafana/grafana:latest
    container_name: grafana
    expose:
      - 3000
    ports:
      - "3000:3000"
    networks:
      - monitoring
```
- Puis reconstruire et relancer le docker compose
- Grafana est accesssible sur http://ip_machine:3000 (login et password par défaut : admin)
- Il ne reste plus qu'à configurer la source de données (Promothéus) et à créer les dashboard (par exemple vous pouvez importer le dashboard https://grafana.com/grafana/dashboards/193 prévu pour docker) 
Pour l'URL mettre l'IP du container avec promotheus avec le port 9090 (pour la trouver docker network inspect monitoring)

-> Félicitations votre applications est maintenant monitorer et ses logs centralisés, elle est presque prête pour la production :) 