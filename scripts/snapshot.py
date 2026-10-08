#!/usr/bin/env python3
"""Capture des preuves sans kubeconfig, Secret, jeton ni adresse du cluster."""
import json
import subprocess
import sys
from datetime import datetime, timezone


def kube(*args):
    try:
        return subprocess.check_output(['kubectl', *args], text=True, timeout=30)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as error:
        print(f'ERREUR kubectl : {error}', file=sys.stderr)
        sys.exit(1)


if kube('config', 'current-context').strip() != 'kind-cicd':
    print('ERREUR : ce lab exige le contexte kind-cicd. Vérifier KUBECONFIG.', file=sys.stderr)
    sys.exit(1)
app = json.loads(kube('-n', 'argocd', 'get', 'application', 'taskflow', '-o', 'json'))
result = {'at': datetime.now(timezone.utc).isoformat(), 'application': {
    'source': app['spec']['source'],
    'sync': app.get('status', {}).get('sync'),
    'health': app.get('status', {}).get('health'),
    'reconciledAt': app.get('status', {}).get('reconciledAt')}}
for kind in ['deployment', 'rollout', 'replicaset', 'service', 'pod']:
    data = json.loads(kube('-n', 'taskflow', 'get', kind, '-o', 'json'))
    items = []
    for obj in data['items']:
        if not obj['metadata']['name'].startswith('taskflow'):
            continue
        spec = obj['spec']
        item = {'name': obj['metadata']['name'], 'status': obj.get('status', {})}
        for key in ['replicas', 'selector', 'strategy']:
            if key in spec:
                item[key] = spec[key]
        containers = spec.get('containers', spec.get('template', {}).get('spec', {}).get('containers', []))
        item['images'] = [c['image'] for c in containers]
        # Les IP internes et détails machine ne sont pas utiles au compte rendu.
        if kind == 'pod':
            item['status'] = {'phase': obj['status']['phase'], 'containers': [
                {'name': c['name'], 'ready': c['ready'], 'restartCount': c['restartCount'], 'imageID': c.get('imageID')}
                for c in obj['status'].get('containerStatuses', [])]}
        items.append(item)
    result[kind] = items
print(json.dumps(result, indent=2, ensure_ascii=False))
