# Dérogation temporaire PSSI-R5 — image du cours

- Date : **8 octobre 2026**.
- Échéance : **15 octobre 2026**, sans renouvellement automatique.
- Responsable du suivi : **Tom PATELAS**.
- Validation : [PR #28 fusionnée](https://github.com/Waddenn/taskflow-gitops/pull/28), sans exigence de revue indépendante dans le ruleset du lab.
- Image : `ghcr.io/9m7fjfpv9k-cyber/taskflow:2.2.0`.
- Digest exclusif : `sha256:007c6d93784684df01a816e63e49d1bd5aa47ff9857f7fb452660ab49455876e`.

Le scan du 8 octobre trouve neuf vulnérabilités HIGH avec correctifs disponibles.
L’image pédagogique contient des dépendances anciennes et appartient au registre de
l’intervenant. Le lab exige de conserver ce registre et la version 2.2.0.
La dérogation permet de terminer l’exercice sur le cluster local ; elle **accepte un
risque temporaire**, elle ne corrige pas les bibliothèques et n’affirme pas que les failles
sont inexploitables. Elle ne vaut pas pour une mise en production réelle.

Mesures présentes : image exécutée sous UID 10001, contrainte runAsNonRoot, Service
ClusterIP dans le cluster local kind-cicd. Ces mesures ne suppriment pas les failles applicatives.
L’accessibilité Internet de toute l’infrastructure n’est pas auditée par ce lab.

## Exceptions individuelles

| CVE | Bibliothèque installée | Version corrigée selon Trivy | Gravité |
| --- | --- | --- | --- |
| [CVE-2025-62727](https://avd.aquasec.com/nvd/cve-2025-62727) | starlette 0.41.3 | 0.49.1 | HIGH |
| [CVE-2026-48818](https://avd.aquasec.com/nvd/cve-2026-48818) | starlette 0.41.3 | 1.1.0 | HIGH |
| [CVE-2026-54283](https://avd.aquasec.com/nvd/cve-2026-54283) | starlette 0.41.3 | 1.3.1 | HIGH |
| [CVE-2025-66418](https://avd.aquasec.com/nvd/cve-2025-66418) | urllib3 1.26.20 | 2.6.0 | HIGH |
| [CVE-2025-66471](https://avd.aquasec.com/nvd/cve-2025-66471) | urllib3 1.26.20 | 2.6.0 | HIGH |
| [CVE-2026-21441](https://avd.aquasec.com/nvd/cve-2026-21441) | urllib3 1.26.20 | 2.6.3 | HIGH |
| [CVE-2026-44431](https://avd.aquasec.com/nvd/cve-2026-44431) | urllib3 1.26.20 | 2.7.0 | HIGH |
| [CVE-2026-97687](https://avd.aquasec.com/nvd/cve-2026-97687) | urllib3 1.26.20 | 2.8.0 | HIGH |
| [CVE-2026-97689](https://avd.aquasec.com/nvd/cve-2026-97689) | urllib3 1.26.20 | 2.8.0 | HIGH |

Les neuf entrées `.trivyignore` comportent `exp:2026-10-15`. Le scanner enregistre
un rapport brut **sans exception**, puis applique le fichier uniquement au digest ci-dessus.
Toute autre image est scannée sans ces dérogations. Les nouveaux identifiants ne sont
pas ignorés. Une liste vide d’images ou une erreur du scanner fait échouer le check.
Les rapports finaux conservent les résultats supprimés via `--show-suppressed`.

Avant l’échéance : obtenir une image corrigée du registre autorisé, vérifier la compatibilité
FastAPI/Starlette et les appels urllib3, refaire les tests puis supprimer ces exceptions par PR.
À expiration, les CVE encore détectées redeviennent bloquantes automatiquement.

Référence du mécanisme d’expiration : [documentation officielle Trivy](https://trivy.dev/docs/dev/configuration/filtering/#trivyignore).
