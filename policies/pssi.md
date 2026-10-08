# Mini-PSSI TaskFlow — règles applicables à la production

Ces règles sont vérifiées automatiquement sur chaque Pull Request (Policy as Code).
Une règle non respectée **bloque le merge**.

| Règle | Exigence | Pourquoi | Vérifiée par |
| --- | --- | --- | --- |
| PSSI-R1 | Toute image a un tag explicite, jamais `latest` | Savoir exactement ce qui tourne, pouvoir revenir en arrière | conftest |
| PSSI-R2 | Les images viennent uniquement du registre `ghcr.io/9m7fjfpv9k-cyber/` | Pas d'image inconnue en production | conftest |
| PSSI-R3 | Chaque conteneur a une limite de mémoire | Un conteneur ne doit pas pouvoir épuiser le nœud | conftest |
| PSSI-R4 | Les pods ne tournent jamais en root (`runAsNonRoot: true`) | Limiter l'impact d'une compromission | conftest |
| PSSI-R5 | Aucune vulnérabilité HIGH ou CRITICAL corrigeable dans les images déployées | Ne pas livrer une faille connue et réparable | Trivy |

Toute exception doit être écrite, justifiée, datée et limitée dans le temps
(fichier `.trivyignore` commenté pour PSSI-R5), et validée en PR.


## Périmètre du lab et preuve

Les règles R1–R4 couvrent les conteneurs et initContainers des Deployment, Rollout,
StatefulSet et DaemonSet présents dans `apps/`. R5 scanne les mêmes images.
Ce périmètre reprend les workloads de production du support : les Jobs auxiliaires k6
embarqués dans l’AnalysisTemplate ne sont pas couverts, ni les images d’Argo CD ou du cluster.
Cette politique CI n’est pas un contrôleur d’admission Kubernetes.

La [dérogation R5 limitée au digest du cours](exceptions.md) expire le 15 octobre 2026.
Les bibliothèques vulnérables ne sont pas corrigées par cette dérogation.
