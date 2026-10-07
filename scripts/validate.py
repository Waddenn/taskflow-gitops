#!/usr/bin/env python3
"""Contrôles hors cluster des invariants du lab (PyYAML requis)."""
from pathlib import Path
import re
import sys
import yaml


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(root):
    for folder in ['apps/taskflow', 'exemples/bluegreen', 'exemples/canary']:
        docs = [yaml.safe_load(p.read_text()) for p in (root / folder).glob('*.yaml')]
        workloads = [d for d in docs if d['kind'] in ('Deployment', 'Rollout')]
        require(
            len(workloads) == 1,
            f'{folder}: un seul contrôleur attendu',
        )
        workload = workloads[0]
        spec = workload['spec']
        require(
            spec['replicas'] == 4,
            f'{folder}: 4 replicas requis',
        )
        require(
            spec['selector']['matchLabels'] == spec['template']['metadata']['labels'],
            'Labels du contrôleur et des pods incohérents',
        )
        container = spec['template']['spec']['containers'][0]
        require(
            re.fullmatch('ghcr\\.io/9m7fjfpv9k-cyber/taskflow:(1\\.0\\.0|1\\.1\\.0|2\\.0\\.0|2\\.1\\.0)', container['image']),
            'Image TaskFlow ou registre non autorisé',
        )
        for probe in ['readinessProbe', 'livenessProbe']:
            require(
                container[probe]['httpGet'] == {'path': '/health', 'port': 'http'},
                'Probe attendue sur /health et le port http',
            )
        services = {d['metadata']['name']: d for d in docs if d['kind'] == 'Service'}
        for service in services.values():
            require(
                service['spec']['selector'] == {'app': 'taskflow'},
                'Sélecteur du Service incorrect',
            )
            require(
                service['spec']['ports'][0]['targetPort'] == 'http',
                'Port cible du Service incorrect',
            )
        if workload['kind'] == 'Rollout':
            strategy = spec['strategy']
            require(
                len(strategy) == 1,
                'Une seule stratégie de rollout est attendue',
            )
            if 'blueGreen' in strategy:
                bg = strategy['blueGreen']
                require(
                    bg['activeService'] in services and bg['previewService'] in services,
                    'Services actif et preview requis',
                )
                require(
                    bg['autoPromotionEnabled'] is False,
                    'La promotion Blue-Green doit rester manuelle',
                )
                require(
                    bg['scaleDownDelaySeconds'] == 30,
                    'Délai Blue-Green attendu : 30 secondes',
                )
            else:
                require(
                    strategy['canary']['steps'] == [{'setWeight': 25}, {'pause': {}}, {'setWeight': 50}, {'pause': {'duration': '60s'}}, {'setWeight': 75}, {'pause': {'duration': '30s'}}],
                    'Paliers Canary attendus : 25, 50, 75 avec pauses',
                )
        print(f"OK {folder}: {workload['kind']}, {container['image']}")
    app = yaml.safe_load((root / 'argocd/application.yaml').read_text())['spec']
    require(
        app['source']['targetRevision'] == 'main',
        'Branche Argo CD attendue : main',
    )
    require(
        app['source']['path'] == 'apps/taskflow',
        'Chemin Argo CD attendu : apps/taskflow',
    )
    require(
        'VOTRE-PSEUDO' not in app['source']['repoURL'],
        'Personnaliser le dépôt Git',
    )
    require(
        app['destination']['namespace'] == 'taskflow',
        'Namespace attendu : taskflow',
    )
    require(
        app['syncPolicy']['automated'] == {'prune': True, 'selfHeal': True},
        'Activer prune et selfHeal',
    )
    print('OK Application: main, prune, selfHeal')


if __name__ == '__main__':
    try:
        validate(Path(__file__).resolve().parents[1])
    except (ValueError, KeyError, TypeError, yaml.YAMLError) as error:
        print(f'ERREUR : {error}', file=sys.stderr)
        sys.exit(1)
