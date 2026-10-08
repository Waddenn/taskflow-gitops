import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

for (const folder of ['apps/taskflow', 'exemples/robustesse']) {
  const yaml = fs.readFileSync(`${folder}/configmap-k6.yaml`, 'utf8');
  const code = yaml.split('  robustesse.js: |\n')[1]
    .replace(/^    /gm, '').replace(/^import .*;\n/gm, '')
    .replace(/export default function/g, 'function scenario')
    .replace(/export /g, '');
  function run(pods, hash = 'newhash') {
    let calls = 0;
    const ctx = { __ENV: { EXPECTED_HASH: hash }, console: { log() {} },
      sleep() {}, check() {}, http: { get(url) {
        assert.match(url, /\/health$/);
        const pod = pods[Math.min(calls++, pods.length - 1)];
        return { status: 200, json: () => pod };
      } } };
    vm.runInNewContext(code + '\nif (!options.noConnectionReuse) throw Error("keep-alive actif"); setup();', ctx);
    return calls;
  }
  assert.throws(() => run(['taskflow-oldhash-abc']), /révision attendue/);
  assert.equal(run(['taskflow-newhash-abc']), 3);
  assert.equal(run(['taskflow-oldhash-abc', 'taskflow-newhash-abc', 'taskflow-oldhash-abc', 'taskflow-newhash-abc']), 6);
  assert.equal(run(['taskflow-oldhash-abc'], ''), 0);
  console.log(`OK ${folder}: ancienne révision refusée, convergence attendue, charge manuelle conservée`);
}
