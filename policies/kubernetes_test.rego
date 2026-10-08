package main
import rego.v1

valid := {"kind": "Rollout", "metadata": {"name": "taskflow"}, "spec": {"template": {"spec": {
    "securityContext": {"runAsNonRoot": true},
    "containers": [{"name": "app", "image": "ghcr.io/9m7fjfpv9k-cyber/taskflow:2.2.0", "resources": {"limits": {"memory": "256Mi"}}}]
}}}}

refuse(obj, rule) if {
    messages := deny with input as obj
    some msg in messages
    startswith(msg, rule)
}

test_valide if { messages := deny with input as valid; count(messages) == 0 }
test_tag_absent if {
    obj := json.patch(valid, [{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value": "ghcr.io/9m7fjfpv9k-cyber/taskflow"}])
    refuse(obj, "PSSI-R1")
}
test_latest if {
    obj := json.patch(valid, [{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value": "ghcr.io/9m7fjfpv9k-cyber/taskflow:latest"}])
    refuse(obj, "PSSI-R1")
}
test_registre if {
    obj := json.patch(valid, [{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value": "nginx:1.27"}])
    refuse(obj, "PSSI-R2")
}
test_memoire if {
    obj := json.patch(valid, [{"op": "remove", "path": "/spec/template/spec/containers/0/resources/limits/memory"}])
    refuse(obj, "PSSI-R3")
}
test_non_root_absent if {
    obj := json.patch(valid, [{"op": "remove", "path": "/spec/template/spec/securityContext"}])
    refuse(obj, "PSSI-R4")
}
test_non_root_false if {
    obj := json.patch(valid, [{"op": "replace", "path": "/spec/template/spec/securityContext/runAsNonRoot", "value": false}])
    refuse(obj, "PSSI-R4")
}
test_override_root if {
    obj := json.patch(valid, [{"op": "add", "path": "/spec/template/spec/containers/0/securityContext", "value": {"runAsNonRoot": false}}])
    refuse(obj, "PSSI-R4")
}
test_uid_zero if {
    obj := json.patch(valid, [{"op": "add", "path": "/spec/template/spec/containers/0/securityContext", "value": {"runAsUser": 0}}])
    refuse(obj, "PSSI-R4")
}
test_init_container if {
    obj := json.patch(valid, [{"op": "add", "path": "/spec/template/spec/initContainers", "value": [{"name": "init", "image": "nginx:latest"}]}])
    refuse(obj, "PSSI-R1")
    refuse(obj, "PSSI-R2")
    refuse(obj, "PSSI-R3")
}
test_service_hors_perimetre if {
    messages := deny with input as {"kind": "Service", "metadata": {"name": "taskflow"}}
    count(messages) == 0
}
