# TP7 : Administrer les conteneurs en centralisant les logs et en mettant en place du monitoring

Ce TP vise à mettre en place une réponse à deux besoin : centraliser et analyser les logs d'une part et monitorer nos conteneurs docker d'autre part.
Nous allons utiliser la stack ELK pour le premier besoin, et une suite composée de cAdvisor, Promotheus et Grafana pour le besoin de monitoring.

## Centralisation des logs

### MIse en place d'une application ELK
- POur cela créer un docker compose contenant :
```
elasticsearch:
    image: elasticsearch:2.1.1
    volumes:
            - /srv/elasticsearch/data:/usr/share/elasticsearch/data
    ports:
            - "9200:9200"

logstash:
    image: logstash:2.1.1
    environment:
            TZ: Europe/Paris
    expose:
            - "12201"
    ports:
            - "12201:12201"
            - "12201:12201/udp"
    volumes:
            - ./conf:/conf
    links:
            - elasticsearch:elasticsearch
    command: logstash -f /conf/gelf.conf

kibana:
    image: kibana:4.3
    links:
            - elasticsearch:elasticsearch
    ports:
            - "5601:5601"
```
- Un fichier de configuration pour logstash est nécessaire, créer un dossier conf, puis à l'intérieur de ce dossier un fichier nommé gelf.conf avec le contenu suivant
```
input {
  gelf {
    type => docker
    port => 12201
  }
}

output {
  elasticsearch {
    hosts => elasticsearch
  }
}
```
- Il ne reste plus qu'à le lancer avec un docker-compose up
- Une fois le démarrage terminé, vérifier en vous rendant sur :
http://ip_machine:5601/status qui affiche elastic search
- Kibana est accessible à l'adresse : http://ip_machine:5601  mais pour l'instant sans donnée il ne permet rien
- L'environnement est prêt, il faut maintenant l'alimenter en données

### Envoyer des données à ELK
- Docker supporte le format GELF (GraylogExtendedLogFormat) qui est utilisé par graylog ou logstash, et qui permet au conteneur d'envoyer directement les logs à un de ces outils
- Pour cela utiliser l'option de driver de log prévu à cet effet
```
--log-driver=gelf --log-opt gelf-address=udp://ip_machine:12201
```
- Par exemple :
```
docker run --log-driver=gelf --log-opt gelf-address=udp://192.168.10.2:12201 debian bash -c 'seq 1 10'
```
- Pour vérifier que cela fonctionne, retourner sur la page de kibana, et valider le formulaire (cela indique que Kibana a bien reçu des données)
- Cherchez dans l'interface de kibana ou sont afficher les logs de notre conteneur ?
- Reprenez le docker-compose du tp 5 et ajouter lui les options pour envoyer les logs à logstash, puis relancez le et aller vérifier que les logs apparaissent bien dans kibana


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
- Démarrer le conteneur (docker-compose up)
- En allant sur : http://ip_machine:8005 vous pourrez visualiser les métriques de vos conteneurs

### Ajout de promotheus pour rendre configurable notre supervision
- Pour aller plus loin et rendre cela configuration, ajouter Promotheus au docker-compose :
```
prometheus:
      image: prom/prometheus:v2.0.0
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
- Créer un dossier docker/promotheus et à l'intérieur de ce dossier un fichier promotheus.yml (qui sert pour la configuration) avec le contenu suivant :
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
- Relancer un build et un up sur le docker-compose
- Promotheus est accessible sur : http://ip_machine:9090/targets
- On peut alors vérifier le statut de nos conteneurs

### Ajouter des dashboard avec Grafana

- Ajouter alors l'interface pour créer et visualiser des dashboard grafana au docker compose :
```
 grafana:
    image: grafana/grafana:4.6.2
    container_name: grafana
    volumes:
      - grafana-data:/var/lib/grafana
    expose:
      - 3000
    ports:
      - "3000:3000"
    networks:
      - monitoring

volumes:
...
  grafana-data: {}
```
- Puis reconstruire et relancer le docker compose
- Grafana est accesssible sur http://ip_machine:3000 (login et password par défaut : admin)
- Il ne reste plus qu'à configurer la source de données (Promothéus) et à créer les dashboard (par exemple vous pouvez importer le dashboard https://grafana.com/grafana/dashboards/193 prévu pour docker)

-> Félicitations votre applications est maintenant monitorer et ses logs centralisés, elle est presque prête pour la production :) 