# Rejouer les exercices J2

Chaque modification de `apps/taskflow` passe par une branche, une PR, les checks,
puis une fusion dans `main`. Les commandes de promotion et d'abandon agissent sur
le déroulement du Rollout ; elles ne remplacent pas une correction de Git.

## Préparer le terminal

```bash
export KUBECONFIG="$PWD/.local/kubeconfig"
export PATH="$PWD/.local/bin:$HOME/.local/bin:$PATH"
source scripts/check-context.sh
kubectl -n argocd get application taskflow
```

Attendre séparément `Synced` et `Healthy`. Pendant une pause manuelle du Rollout,
`Suspended` est normal. Pour suivre :

```bash
kubectl argo rollouts get rollout taskflow -n taskflow --watch
./scripts/observe.sh taskflow 100
python3 scripts/snapshot.py
```

## Matin : Deployment, dérive et retour arrière

1. Partir du `deployment.yaml` initial, image `1.0.0`, 4 replicas et Service.
2. Par PR, remplacer seulement le tag par `2.0.0`. Chronométrer depuis la fusion
   jusqu'à la réconciliation du SHA fusionné et à la disponibilité des 4 replicas.
3. `kubectl -n taskflow scale deployment taskflow --replicas=1`. Observer le retour
   à 4 demandé par Git. Puis injecter une dérive d'image :
   `kubectl -n taskflow set image deployment/taskflow taskflow=ghcr.io/9m7fjfpv9k-cyber/taskflow:1.1.0`.
   Attendre le retour à `2.0.0` et vérifier les pods, pas seulement la spec.
4. Créer une PR de revert du commit de release : Git revient à `1.0.0`, Argo CD suit.
5. Bonus : supprimer `service.yaml` par PR, vérifier sa disparition (`prune`),
   puis restaurer ce fichier par une nouvelle PR avant la suite.

## Après-midi : Blue-Green

1. Par PR, supprimer `apps/taskflow/deployment.yaml`, copier les trois fichiers de
   `exemples/bluegreen/` dans `apps/taskflow/`. Attendre le Rollout `Healthy`.
2. Par PR, passer le Rollout à `1.1.0`. Attendre la pause.
3. `./scripts/observe.sh taskflow 100` puis
   `./scripts/observe.sh taskflow-preview 100`. Compter les pods Ready : 4 anciens +
   4 nouveaux. Les probes vérifient `/health` ; les observations interrogent `/`.
4. `kubectl argo rollouts promote taskflow -n taskflow`.
   Observer la production `1.1.0` puis la réduction des anciens pods après 30 s.

## Après-midi : Canary et incident

1. Par PR, remplacer le Rollout avec `exemples/canary/rollout.yaml`, conserver
   l'image `1.1.0`, restaurer le Service de `exemples/canary/service.yaml` et supprimer
   `service-preview.yaml`. Vérifier que le Service ne sélectionne plus le hash
   propre au Blue-Green.
2. Par PR, passer à `2.0.0`. Observer la pause à 25 % et la répartition 1 nouveau /
   3 anciens. `./scripts/observe.sh taskflow 100`.
3. `kubectl argo rollouts promote taskflow -n taskflow`. Observer 50 % pendant 60 s,
   75 % pendant 30 s puis 100 %. Ne pas utiliser `--full`, qui court-circuiterait les
   pauses à mesurer. Le pourcentage de requêtes reste statistique sans traffic router.
4. Par PR, passer à `2.1.0`. À 25 %, observer `/` et `/health` :
   `./scripts/observe.sh taskflow 200` et `./scripts/observe.sh taskflow 100 /health`.
5. `kubectl argo rollouts abort taskflow -n taskflow`. Observer le trafic revenu à
   `2.0.0`, la spec toujours en `2.1.0`, et la santé dégradée du Rollout.
6. Faire une PR de revert vers `2.0.0`. Attendre `Synced` + `Healthy` et contrôler
   les codes HTTP. Ne pas laisser Git demander durablement la version défectueuse.

Les résultats de référence et leurs limites sont dans le journal du README.
