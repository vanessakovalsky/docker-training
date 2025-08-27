# Déploiement multi-environnements

## Pré-requis
- installer minikube sur son poste : https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download
- Insaller Kustomize : https://kustomize.io/ 

## Objectif
- Gérer les environnements dev/staging/prod

**Structure attendue** :
```
environments/
├── dev/
│   ├── docker-compose.override.yml
│   └── .env
├── staging/
│   ├── kustomization.yml
│   └── patches/
└── prod/
    ├── kustomization.yml
    ├── patches/
    └── secrets/
```

## Consignes

1. Configurez trois environnements distincts
2. Utilisez Kustomize pour Kubernetes
3. Gérez les secrets de manière sécurisée
4. Automatisez le déploiement par environnement
