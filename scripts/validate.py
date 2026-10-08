#!/usr/bin/env python3
"""Contrôles hors cluster des invariants du lab (PyYAML requis)."""
from pathlib import Path
import re
import yaml

root = Path(__file__).resolve().parents[1]
for folder in ['apps/taskflow', 'exemples/bluegreen', 'exemples/canary', 'exemples/robustesse']:
    docs = [yaml.safe_load(p.read_text()) for p in (root / folder).glob('*.yaml')]
    workloads = [d for d in docs if d['kind'] in ('Deployment', 'Rollout')]
    assert len(workloads) == 1, f'{folder}: un seul contrôleur attendu'
    workload = workloads[0]
    spec = workload['spec']
    if folder == 'apps/taskflow':
        assert workload['kind'] == 'Rollout', 'J3 A : Rollout requis, aucun Deployment'
        assert spec['strategy']['canary']['canaryService'] == 'taskflow-canary'
    assert spec['replicas'] == 4, f'{folder}: 4 replicas requis'
    assert spec['selector']['matchLabels'] == spec['template']['metadata']['labels']
    container = spec['template']['spec']['containers'][0]
    assert re.fullmatch(r'ghcr.io/9m7fjfpv9k-cyber/taskflow:(1\.0\.0|1\.1\.0|2\.0\.0|2\.1\.0)', container['image'])
    for probe in ['readinessProbe', 'livenessProbe']:
        assert container[probe]['httpGet'] == {'path': '/health', 'port': 'http'}
    services = {d['metadata']['name']: d for d in docs if d['kind'] == 'Service'}
    for service in services.values():
        assert service['spec']['selector'] == {'app': 'taskflow'}
        assert service['spec']['ports'][0]['targetPort'] == 'http'
    if workload['kind'] == 'Rollout':
        strategy = spec['strategy']
        assert len(strategy) == 1
        if 'blueGreen' in strategy:
            bg = strategy['blueGreen']
            assert bg['activeService'] in services and bg['previewService'] in services
            assert bg['autoPromotionEnabled'] is False
            assert bg['scaleDownDelaySeconds'] == 30
        elif 'canaryService' in strategy.get('canary', {}):
            assert workload['kind'] == 'Rollout'
            canary = strategy['canary']
            assert canary['canaryService'] == 'taskflow-canary'
            assert canary['canaryService'] in services
            assert canary['steps'] == [
                {'setWeight': 25},
                {'analysis': {
                    'templates': [{'templateName': 'robustesse-k6'}],
                    'args': [{'name': 'cible', 'value': 'http://taskflow-canary'}]}},
                {'setWeight': 50}, {'pause': {'duration': '30s'}},
                {'setWeight': 75}, {'pause': {'duration': '30s'}}]
            analysis = next(d for d in docs if d['kind'] == 'AnalysisTemplate')
            assert analysis['metadata']['name'] == 'robustesse-k6'
            assert analysis['spec']['args'] == [{'name': 'cible'}]
            job = analysis['spec']['metrics'][0]['provider']['job']['spec']
            assert job['backoffLimit'] == 0
            pod = job['template']['spec']
            assert pod['restartPolicy'] == 'Never'
            k6 = pod['containers'][0]
            assert k6['args'] == ['run', '/scripts/robustesse.js']
            assert k6['env'] == [{'name': 'TARGET', 'value': '{{args.cible}}'}]
            assert k6['volumeMounts'] == [{'name': 'scripts', 'mountPath': '/scripts'}]
            assert pod['volumes'] == [
                {'name': 'scripts', 'configMap': {'name': 'k6-robustesse'}}]
            config = next(d for d in docs if d['kind'] == 'ConfigMap')
            assert config['metadata']['name'] == 'k6-robustesse'
            scenario = config['data']['robustesse.js']
            for required in ["vus: 5", "duration: '60s'", "'rate<0.02'",
                             "'p(95)<250'", 'http.get(`${TARGET}/tasks`)']:
                assert required in scenario, f'{folder}: scénario k6 incomplet'
        else:
            assert strategy['canary']['steps'] == [
                {'setWeight': 25}, {'pause': {}}, {'setWeight': 50},
                {'pause': {'duration': '60s'}}, {'setWeight': 75},
                {'pause': {'duration': '30s'}}]
    print(f'OK {folder}: {workload["kind"]}, {container["image"]}')
app = yaml.safe_load((root / 'argocd/application.yaml').read_text())['spec']
assert app['source']['targetRevision'] == 'main'
assert app['source']['path'] == 'apps/taskflow'
assert 'VOTRE-PSEUDO' not in app['source']['repoURL']
assert app['destination']['namespace'] == 'taskflow'
assert app['syncPolicy']['automated'] == {'prune': True, 'selfHeal': True}
print('OK Application: main, prune, selfHeal')
