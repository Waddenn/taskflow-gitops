#!/usr/bin/env bash
# À sourcer avant toute opération du lab.
export PATH="${HOME}/.local/bin:${PATH}"
if [[ "$(kubectl config current-context)" != "kind-cicd" ]]; then
  echo 'ERREUR : ce lab exige le contexte kind-cicd. Vérifier KUBECONFIG.' >&2
  exit 1
fi
