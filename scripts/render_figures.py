#!/usr/bin/env python3
"""Figures du README, calculées uniquement à partir des preuves enregistrées.
Installer matplotlib==3.10.8 pour les régénérer.
"""
import re
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/images'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.titleweight': 'bold', 'figure.facecolor': 'white'})


def counts(name):
    text = (ROOT / 'docs/evidence' / f'{name}.txt').read_text()
    return [(int(n), v, code) for n, v, code in re.findall(r'(\d+) version=(\S+) http=(\d+)', text)]


fig, ax = plt.subplots(figsize=(11, 5.4), layout='constrained')
labels = ['25 %\npause manuelle', '50 %\npause 60 s', '75 %\npause 30 s', '100 %\nstable']
for i, step in enumerate([25, 50, 75, 100]):
    data = counts(f'10-canary-{step}')
    total = sum(n for n, _, _ in data)
    bottom = 0
    for version, color in [('1.1.0', '#4263a8'), ('2.0.0', '#0a927f')]:
        value = sum(n for n, v, _ in data if v == version)
        percent = value / total * 100
        ax.bar(i, percent, bottom=bottom, color=color, width=.6, label=version if i == 0 else None)
        if value:
            ax.text(i, bottom + percent / 2, f'{value}/{total}', ha='center', va='center', color='white', fontweight='bold')
        bottom += percent
ax.set_xticks(range(4), labels)
ax.set_ylim(0, 107)
ax.set_ylabel('Requêtes observées (%)')
ax.set_title('Canary : le trafic mesuré à chaque palier', loc='left', pad=20)
ax.legend(title='Version servie', loc='upper left', bbox_to_anchor=(1.01, 1))
fig.supxlabel('Échantillons réels via le Service Kubernetes · pourcentages non garantis sans traffic router', fontsize=10)
fig.savefig(OUT / 'canary-traffic.png', dpi=180)
plt.close(fig)

fig, ax = plt.subplots(figsize=(11, 4.8), layout='constrained')
stages = [('11-bug-http', '2.1.0 au palier 25 %\nroute métier /'),
          ('11-bug-health', 'Même canary\nprobe /health'),
          ('12-aborted', 'Après abort\nroute métier /'),
          ('13-final-2.0.0', 'Après revert Git\nroute métier /')]
for i, (name, label) in enumerate(stages):
    data = counts(name); total = sum(n for n, _, _ in data)
    failed = sum(n for n, _, code in data if code != '200')
    rate = failed / total * 100
    ax.barh(i, rate, color='#d94b4b' if failed else '#0a927f', height=.55)
    ax.text(rate + 1, i, f'{failed}/{total} erreurs ({rate:.1f} %)', va='center', fontsize=11)
ax.set_yticks(range(len(stages)), [label for _, label in stages])
ax.invert_yaxis()
ax.set_xlim(0, 100)
ax.set_xlabel('Réponses autres que HTTP 200 (%)')
ax.set_title('Incident 2.1.0 : les probes ne voient pas le défaut métier', loc='left', pad=20)
fig.supxlabel('Données des fichiers docs/evidence/*.txt · échantillons distincts, pas un test de charge', fontsize=10)
fig.savefig(OUT / 'incident-http.png', dpi=180)
plt.close(fig)
print('Figures enregistrées dans docs/images/')
