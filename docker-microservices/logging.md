# Logging centralisé avec ELK

**Objectif** : Centraliser les logs de tous les microservices

**Instructions** :
1. Déployer la stack ELK (Elasticsearch, Logstash, Kibana)
2. Configurer les microservices pour envoyer des logs structurés
3. Créer des dashboards Kibana
4. Configurer des alertes sur les erreurs

```yaml
# docker-compose.elk.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
  
  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch
  
  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```
