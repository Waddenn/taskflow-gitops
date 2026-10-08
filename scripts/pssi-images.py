#!/usr/bin/env python3
"""Scanner toutes les images des workloads de production, sans résultat vide vert."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
KINDS = {'Deployment', 'Rollout', 'StatefulSet', 'DaemonSet'}
TRIVY = 'aquasec/trivy:0.75.0@sha256:af6acf9a6b85dfe389a1941505c0ce9efef52a4719635e1a962f022a3d855daa'
EXCEPTION_IMAGE = 'ghcr.io/9m7fjfpv9k-cyber/taskflow@sha256:007c6d93784684df01a816e63e49d1bd5aa47ff9857f7fb452660ab49455876e'


def images():
    result = set()
    for path in (ROOT / 'apps').rglob('*.yaml'):
        for doc in yaml.safe_load_all(path.read_text()):
            if not doc or doc.get('kind') not in KINDS:
                continue
            spec = doc['spec']['template']['spec']
            for key in ('containers', 'initContainers'):
                for container in spec.get(key, []):
                    result.add(container['image'])
    if not result:
        raise ValueError('PSSI-R5 : aucune image de production trouvée')
    return sorted(result)


def main():
    reports = (ROOT / 'reports/pssi').resolve()
    cache = (ROOT / '.local/trivy-cache').resolve()
    reports.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / '.trivyignore', reports / 'exceptions.ignore')
    # Le scanner ne reçoit que les rapports et le cache, pas le dépôt ni son kubeconfig.
    command = ['docker', 'run', '--rm', '-v', f'{reports}:/reports:Z',
               '-v', f'{cache}:/root/.cache/trivy:Z', TRIVY, 'image', '--quiet',
               '--scanners', 'vuln', '--severity', 'HIGH,CRITICAL', '--ignore-unfixed', '--format', 'json']
    summary = []
    failed = False
    for i, image in enumerate(images(), 1):
        raw = f'{i:02d}-raw.json'
        final = f'{i:02d}-gate.json'
        subprocess.run(command + ['--ignorefile', '/dev/null', '--exit-code', '0',
                                 '--output', f'/reports/{raw}', image], check=True)
        data = json.loads((reports / raw).read_text())
        digests = data.get('Metadata', {}).get('RepoDigests', [])
        if not digests:
            raise ValueError(f'Image sans digest vérifiable : {image}')
        immutable = digests[0]
        ignore = '/reports/exceptions.ignore' if immutable == EXCEPTION_IMAGE else '/dev/null'
        print(f'Image : {image}\nDigest : {immutable}\nExceptions : {ignore}', flush=True)
        result = subprocess.run(command + ['--ignorefile', ignore, '--show-suppressed', '--exit-code', '1',
                                          '--output', f'/reports/{final}', immutable])
        failed |= result.returncode != 0
        count = sum(len(r.get('Vulnerabilities', [])) for r in data.get('Results', []))
        summary.append({'image': image, 'digest': immutable, 'raw_findings': count,
                        'exception_file': ignore, 'exit_code': result.returncode})
    (reports / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
