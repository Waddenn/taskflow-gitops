# Origine des visuels

- `bluegreen-paused.jpg` et `bluegreen-replicas.jpg` : captures réelles du dashboard
  Argo Rollouts v1.10.0, cluster `kind-cicd`, avant promotion de 1.1.0.
- `canary-paused.jpg` : capture réelle au palier manuel 25 % de la release 2.0.0.
- `canary-aborted.jpg` : capture réelle après abandon de la release 2.1.0, avant revert Git.
- `canary-traffic.png` et `incident-http.png` : graphiques générés à partir des
  mesures brutes dans `docs/evidence/`, sans données simulées.

Régénérer les graphiques : installer `matplotlib==3.10.8` dans un environnement
Python puis lancer `python scripts/render_figures.py` depuis la racine du dépôt.
Les captures ne sont pas des maquettes et n’ont pas été retouchées.
