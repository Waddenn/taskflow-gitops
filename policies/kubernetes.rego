# Mini-PSSI TaskFlow traduite en règles automatiques (Rego, lu par conftest).
# Lancer en local :  conftest test apps/ --policy policies/
package main

import rego.v1

charges_de_travail := {"Deployment", "Rollout", "StatefulSet", "DaemonSet"}

registre_autorise := "ghcr.io/9m7fjfpv9k-cyber/"

# Tous les conteneurs des objets qui font tourner des pods.
conteneurs contains c if {
	charges_de_travail[input.kind]
	some c in input.spec.template.spec.containers
}

# PSSI-R1 : tag explicite, jamais latest.
deny contains msg if {
	some c in conteneurs
	not regex.match(":[A-Za-z0-9_][A-Za-z0-9_.-]*$", split(c.image, "@")[0])
	msg := sprintf("PSSI-R1 : l'image du conteneur '%s' n'a pas de tag explicite (%s)", [c.name, c.image])
}

deny contains msg if {
	some c in conteneurs
	endswith(split(c.image, "@")[0], ":latest")
	msg := sprintf("PSSI-R1 : le conteneur '%s' utilise le tag latest (%s)", [c.name, c.image])
}

# PSSI-R2 : registre autorisé uniquement.
deny contains msg if {
	some c in conteneurs
	not startswith(c.image, registre_autorise)
	msg := sprintf("PSSI-R2 : l'image du conteneur '%s' ne vient pas du registre autorisé (%s)", [c.name, c.image])
}



# R3 : une limite explicite est obligatoire pour chaque conteneur.
deny contains msg if {
    some c in conteneurs
    not c.resources.limits.memory
    msg := sprintf("PSSI-R3 : le conteneur '%s' doit avoir resources.limits.memory", [c.name])
}

# R4 : la contrainte est portée par le pod, pas seulement par l'image.
pod_non_root if {
    input.spec.template.spec.securityContext.runAsNonRoot == true
}

deny contains msg if {
    charges_de_travail[input.kind]
    not pod_non_root
    msg := sprintf("PSSI-R4 : le pod de '%s' doit déclarer securityContext.runAsNonRoot: true", [input.metadata.name])
}

# Un conteneur ne peut pas annuler la contrainte définie au niveau du pod.
deny contains msg if {
    some c in conteneurs
    c.securityContext.runAsNonRoot == false
    msg := sprintf("PSSI-R4 : le conteneur '%s' annule runAsNonRoot", [c.name])
}

deny contains msg if {
    some c in conteneurs
    c.securityContext.runAsUser == 0
    msg := sprintf("PSSI-R4 : le conteneur '%s' demande explicitement l'UID root", [c.name])
}

deny contains msg if {
    charges_de_travail[input.kind]
    input.spec.template.spec.securityContext.runAsUser == 0
    msg := "PSSI-R4 : le pod demande explicitement l'UID root"
}

# Les initContainers font partie de la même charge de travail.
conteneurs contains c if {
    charges_de_travail[input.kind]
    some c in input.spec.template.spec.initContainers
}
