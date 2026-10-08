# J3 — Partie A : l’étalon et l’analyse

Travail du 8 octobre 2026, réalisé à partir du LAB J2, limité à la partie A du support J3 (page 10).

## Reprise de J2

Le cluster local avait été supprimé. Il a été recréé avec `scripts/install.sh`,
le kubeconfig dédié `.local/kubeconfig` et le contexte `kind-cicd`.
Argo CD a repris `main` et rétabli TaskFlow **2.0.0**, quatre pods prêts,
avec l’état **Synced / Healthy**, avant toute modification de la stratégie.
L’[état de référence](evidence/j3-a/etat-reference.json) conserve cette preuve.

Les supports upstream ont été synchronisés depuis le commit `17d7918`.
Le README et les adaptations locales de l’installateur du J2 sont conservés.
Les exemples PSSI récupérés restent des supports : aucun workflow de sécurité n’est activé.

## Mesure de référence

```bash
export KUBECONFIG="$PWD/.local/kubeconfig"
export PATH="$PWD/.local/bin:$HOME/.local/bin:$PATH"
./scripts/charge.sh http://taskflow
```

Le scénario exécute des requêtes sur `/tasks`, avec **5 utilisateurs virtuels pendant 30 secondes**.
Les seuils sont stricts : **erreurs < 2 %** et **p95 < 250 ms**.
Le [résultat brut k6](evidence/j3-a/charge-2.0.0.txt) contient la mesure sur 2.0.0.

Résultat : **738 requêtes, 0 erreur (0,00 %), p95 = 4,23 ms**, seuils respectés
et code de sortie 0. Ce résultat décrit le cluster local au moment du test.

## Analyse automatique

PR : [feat/analyse-auto — #18](https://github.com/Waddenn/taskflow-gitops/pull/18).

Les quatre fichiers du support sont repris dans `apps/taskflow/` :

- `rollout.yaml` : conserve 2.0.0, remplace la pause manuelle à 25 % par l’analyse k6 ;
- `analysis-template.yaml` : exécute un Job k6 sans nouvelle tentative ;
- `configmap-k6.yaml` : stocke le scénario et les seuils ;
- `service-canary.yaml` : cible les pods de la nouvelle révision grâce au sélecteur géré par Argo Rollouts.

Le Service principal existant est conservé. Le J2 utilisait déjà un Rollout :
il n’y avait plus de `deployment.yaml` à supprimer. Un seul Rollout et aucun Deployment
sont attendus dans `apps/taskflow/` et dans le namespace du lab.

Au prochain changement d’image, l’analyse à 25 % devra réussir avant les paliers
50 %, 75 % et 100 %. Un Job en échec provoquera l’abandon automatique.
La configuration seule ne constitue pas une preuve d’abort : cette expérience relève de la partie B.

## Vérifications

```bash
python3 scripts/validate.py
for script in scripts/*.sh; do bash -n "$script"; done
kubectl -n taskflow apply --dry-run=server -f apps/taskflow/
kubectl get crd rollouts.argoproj.io analysistemplates.argoproj.io analysisruns.argoproj.io
kubectl -n taskflow get rollout,deployment
kubectl -n taskflow get analysistemplate,configmap,svc
kubectl -n argocd get application taskflow
```

La CI vérifie la présence d’un seul contrôleur, la version 2.0.0 autorisée,
les étapes du canary, le Service dédié, les liens du Job vers la ConfigMap et les seuils.
Le script de charge refuse un contexte différent de `kind-cicd`.

Preuves : [validation locale](evidence/j3-a/validation.txt),
[validation serveur sans application](evidence/j3-a/dry-run-server.txt),
[CRD installées](evidence/j3-a/crd.txt).

Après fusion de la PR #18, vérification le 8 octobre à 10 h 08 (Paris) :
Argo CD a synchronisé le commit `4af6f7b`, en état **Synced / Healthy**.
TaskFlow reste en **2.0.0**, avec **4/4 pods prêts**, **un Rollout et zéro Deployment**.
L’AnalysisTemplate `robustesse-k6`, la ConfigMap `k6-robustesse` et les deux Services
sont présents. Le sélecteur de `taskflow-canary` correspond au hash du Rollout.
Voir l’[état final](evidence/j3-a/etat-final.json) et la
[vérification finale](evidence/j3-a/verification-finale.json).

Aucun AnalysisRun n’a été créé : la version et le template des pods n’ont pas changé.
L’analyse automatique est configurée pour le prochain déploiement ; seul le test
de référence manuel a été exécuté dans cette partie A.

## Limite de ce rendu

La partie B (incident 2.1.0, abort, revert, passage 2.2.0, postmortem) et la partie C
(PSSI et sécurité) ne sont pas réalisées. Les preuves d’incident J2 existantes
restent des observations J2 et ne démontrent pas un abort automatique J3.
