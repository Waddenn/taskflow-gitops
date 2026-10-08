# Postmortem — TaskFlow 2.1.0 et contrôle de la cible k6

Le 8 octobre 2026, le rejeu de TaskFlow 2.1.0 a été **annulé automatiquement**
au palier 25 % : **27,71 % d’erreurs HTTP** et **p95 de 308,43 ms**.
Argo Rollouts a rétabli quatre pods 2.0.0 sans commande manuelle d’abort ou de promotion.
Le revert Git a ensuite remis l’état souhaité en cohérence. La **2.2.0** a enfin été
promue automatiquement à 100 % : **0 % d’erreurs, p95 7,09 ms**, Synced / Healthy.

Un premier essai avait toutefois été validé à tort : k6 avait testé la stable.
Ce résultat est conservé et expliqué ici ; il ne constitue pas une preuve de robustesse.

## Impact et périmètre

| Champ | Observation |
| --- | --- |
| Environnement | Cluster local `kind-cicd`, namespace `taskflow`, aucun trafic utilisateur externe mesuré |
| Version défectueuse | `ghcr.io/9m7fjfpv9k-cyber/taskflow:2.1.0` |
| PR initiale / rejeu | [#21](https://github.com/Waddenn/taskflow-gitops/pull/21) / [#24](https://github.com/Waddenn/taskflow-gitops/pull/24) |
| Analyse probante | `taskflow-df976ccb5-4-1` — `Failed` |
| Job probant | `232965c9-7d69-48d1-bdb7-866ce4c801f4.test-de-charge-k6.1` — `Failed`, sortie k6 99 |
| Exposition potentielle du rejeu | Environ **76 s**, entre 11:06:51 et 11:08:07, d’après les pods prêts observés toutes les ≈2,3 s |
| Part exposée pendant le rejeu | 1 pod sur 4, soit environ 25 % des nouvelles connexions ; aucun routeur ne garantit un pourcentage exact |
| Charge mesurée | 5 VU pendant 60 s, après vérification de la révision ; 595 requêtes `/tasks`, 166 échecs ; 599 requêtes HTTP avec les 4 requêtes de préparation |
| Taux mesuré | `http_req_failed` = 166/599 = **27,71 %** ; sur `/tasks` seul, 166/595 = **27,90 %** |
| Résolution immédiate | Échec k6 → Job Failed → AnalysisRun Failed → `RolloutAborted` → 0 pod canary, 4 pods stables |
| Retour de Git | [PR #25](https://github.com/Waddenn/taskflow-gitops/pull/25), véritable `git revert` |
| Vérification après abort | 200/200 réponses 200 sur `/tasks` ; 200/200 réponses `/health` en version 2.0.0 |

Ces durées décrivent une fenêtre d’exposition possible dans le lab, pas une durée
mesurée d’impact sur de vrais utilisateurs. Lors du **premier essai incorrect**, des pods
2.1.0 prêts ont été observés de 10:58:13 à 11:06:35 (environ 8 min 22 s), avec passage
jusqu’à 100 %. Cet incident supplémentaire est distinct du rejeu automatiquement annulé.

## Chronologie

Heures du 8 octobre 2026, **Europe/Paris (UTC+2)**. Les preuves brutes sont en UTC.

| Heure | Événement et preuve |
| --- | --- |
| 10:58:13 | Premier canary 2.1.0 prêt ; scénario original sans contrôle d’identité |
| 10:59:28 | Premier AnalysisRun Successful : 0 % d’erreurs, p95 4,70 ms ; faux positif |
| 11:00:46 | La première 2.1.0 atteint Healthy à 100 %, preuve de l’insuffisance du contrôle initial |
| 11:02:23 | Synchronisation du premier revert, PR #22 |
| 11:03:31 | Le test du retour 2.0.0 échoue en mesurant encore 2.1.0 ; même défaut de cible, en sens inverse |
| 11:04:06 | Correction #23 synchronisée ; nouvelle analyse créée automatiquement après modification des arguments |
| 11:04:13 | k6 confirme le pod/hash 2.0.0 ; cette analyse réussit, p95 8,29 ms, 0 % d’erreurs |
| 11:06:37 | Référence 2.0.0 Healthy, quatre pods prêts |
| 11:06:40 | Fusion du rejeu 2.1.0, PR #24 |
| 11:06:51 | Canary prêt et analyse au palier 25 % |
| 11:06:52 | Log k6 : cible `taskflow-df976ccb5-cpnf9`, hash attendu `df976ccb5` |
| 11:07:52 | k6 signale le franchissement des deux seuils |
| 11:08:05 | Événements `MetricFailed`, `AnalysisRunFailed`, `RolloutAborted` |
| 11:08:07 | Aucun pod 2.1.0 prêt observé, quatre pods 2.0.0 prêts |
| 11:08:18 et 11:08:31 | Contrôles HTTP après abort : 200/200 réponses 200 pour chaque route testée |
| 11:09:02 | Revert #25 synchronisé : 2.0.0 Healthy dans Git et le cluster |
| 11:10:04 | Fusion de 2.2.0, PR #26 |
| 11:11:25 | Analyse 2.2.0 Successful, puis paliers 50 % et 75 % |
| 11:12:43 | 2.2.0 à 100 %, quatre pods prêts, Healthy |

La [chronologie complète](evidence/j3-b/timeline-compact.jsonl) conserve les changements
d’état, y compris la progression de 2.2.0. Les événements Kubernetes et les dates de fusion
des PR sont archivés dans [les preuves](evidence/j3-b/).

## Les quatre preuves de l’incident

1. **Révision et image** : [Rollout après abort](evidence/j3-b/rollout-abort-stabilise.txt), révision 4 abandonnée, 2.0.0 stable.
2. **Métrique en échec** : [describe AnalysisRun](evidence/j3-b/taskflow-df976ccb5-4-1-describe.txt), métrique `test-de-charge-k6` Failed.
3. **Mesures k6** : [logs du Job](evidence/j3-b/232965c9-7d69-48d1-bdb7-866ce4c801f4.test-de-charge-k6.1-logs.txt), erreurs et p95 au-dessus des seuils.
4. **Chronologie Kubernetes** : [événements horodatés](evidence/j3-b/events-abort-stabilise.json), en particulier `RolloutAborted` à 09:08:05 UTC.

![Abort automatique de 2.1.0](images/j3-abort-2.1.0.png)

*Rendu en image de la sortie CLI réelle, avec sa source texte conservée ; ce n’est pas une capture du bureau.*

## Composant défaillant et cause racine

Le middleware FastAPI `inject_faults` de **l’image 2.1.0** injecte une pause de 300 ms
et une probabilité d’erreur 500 de 0,3 sur les routes autres que `/health`.
Les valeurs réellement chargées sont `VERSION=2.1.0`, `LATENCY_MS=300`,
`FAILURE_RATE=0.3`. [Code et valeurs lus dans le pod](evidence/j3-b/cause-2.1.0.txt).
Le délai minimal injecté suffit à dépasser le budget p95 de 250 ms.

Les probes ne l’ont pas détecté parce qu’elles interrogent **`/health`, explicitement
exclue de l’injection**. La réponse `status: ok, version: 2.1.0` a été observée dans le pod.
La CI des manifests valide la configuration, mais ne prouve pas le comportement sous charge.

### Pourquoi le premier test a-t-il donné un faux positif ?

Le premier Job était configuré avec `TARGET=http://taskflow-canary`, mais ses requêtes
atteignaient encore la stable. Dans les logs conservés, **588 requêtes `/tasks`** de l’IP
du Job (`10.244.0.20`) sont présentes dans un seul pod 2.0.0, **aucune** dans le pod 2.1.0.
Le [log stable](evidence/j3-b/stable-premier-essai.log), le
[log canary](evidence/j3-b/canary-premier-essai.log) et le
[premier résultat k6](evidence/j3-b/e5da4c39-404e-4857-8a10-c4b6e4ab0fca.test-de-charge-k6.1-logs.txt)
permettent de le vérifier.

Le scénario ouvrait ses connexions pendant le changement de cible du Service et les
réutilisait ensuite. La persistance des connexions vers l’ancienne cible est cohérente avec
ces observations ; l’instant exact de propagation réseau n’a pas été capturé paquet par paquet.
Le défaut démontré est l’absence de vérification de la révision réellement testée.

La PR #23 ajoute `noConnectionReuse: true` et un argument `pod-hash` issu de
`podTemplateHashValue: Latest`. Le setup exige trois réponses `/health` consécutives
portant ce hash avant de commencer la charge. En absence de convergence, il échoue.
Les seuils métier et les 60 secondes demandées restent inchangés.
Les tests en CI couvrent le refus d’une ancienne révision, l’attente de convergence et
la conservation du mode de charge manuelle. Le rejeu réel a ensuite démontré l’échec de 2.1.0.

Références : [options k6, réutilisation des connexions](https://grafana.com/docs/k6/latest/using-k6/k6-options/reference/)
et [arguments d’analyse Argo Rollouts](https://argoproj.github.io/argo-rollouts/features/analysis/).

## Ce qui a fonctionné et actions

Après correction de la cible, les deux seuils ont bloqué la promotion et le contrôleur a
rétabli la stable. L’abort protège le trafic ; le revert en PR rétablit la vérité Git.
Les mesures trompeuses initiales sont conservées pour éviter de confondre un check vert
avec une preuve portant sur la bonne version.

| Action | Responsable | Échéance | État / preuve |
| --- | --- | --- | --- |
| Vérifier le hash cible et désactiver la réutilisation des connexions | Tom PATELAS | 08/10/2026 | Réalisé, PR #23 |
| Couvrir le faux positif par des tests de convergence en CI | Tom PATELAS | 08/10/2026 | Réalisé, `tests/test_k6_setup.mjs` |
| Revert Git après abort | Tom PATELAS | 08/10/2026 | Réalisé, PR #25 |
| Déployer et mesurer la version corrigée 2.2.0 | Tom PATELAS | 08/10/2026 | PR #26, résultat dans le journal J3 B |
| Ajouter un test métier sous charge avant publication d’une image | Tom PATELAS | 09/10/2026 | Proposition, non implémentée dans ce lab |
| Épingler l’image k6 à une version ou un digest pour des mesures reproductibles | Tom PATELAS | 09/10/2026 | Proposition, le support utilise encore `latest` |

La partie C (PSSI, SAST/DAST/IAST) n’est pas réalisée dans ce rendu.
