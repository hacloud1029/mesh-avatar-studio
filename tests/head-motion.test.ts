import { expect, test } from 'vitest';
import fixture from '../samples/miko-qipao/rig.json';
import { parseRig, PARAMS, validateRig } from 'mesh-avatar';
import { createRig } from '../packages/runtime/src/engine/rig.js';

const phys = { gain: 0, bunL: [0, 0], bunR: [0, 0], strands: [] };
const pose = (extra: Record<string, number>) => ({ ...Object.fromEntries(PARAMS.map(p => [p.id, p.def])), ...extra });
function offset(rig: ReturnType<typeof parseRig>, [x, y]: number[], P: ReturnType<typeof pose>) {
  const R = createRig(rig), out = [0, 0];
  R.deformBase(x, y, R.baseWeights(x, y, 0), P, phys, out);
  return [out[0] - x, out[1] - y];
}

test('head parallax scales the per-feature turn offsets linearly', () => {
  const at = (parallax?: number) => {
    const rig = parseRig(fixture);
    if (parallax !== undefined) rig.head.parallax = parallax;
    return offset(rig, [rig.face.nose.cx, rig.face.nose.cy], pose({ angleX: 30, angleY: 10 }));
  };
  const [one, two, three] = [at(1), at(2), at(3)];
  // offset = head turn + parallax * per-feature part
  expect(two[0] - one[0]).not.toBeCloseTo(0, 1);
  expect(three[0] - two[0]).toBeCloseTo(two[0] - one[0], 6);
  expect(three[1] - two[1]).toBeCloseTo(two[1] - one[1], 6);
  // without the field the rig behaves as with parallax 1
  expect(at()).toEqual(one);
});

test('jaw drop sets how far the chin lowers with the mouth open', () => {
  const rig = parseRig(fixture), chin = [rig.face.jaw.cx, rig.face.jaw.cy];
  const P = pose({ mouthOpen: 1 });
  const before = offset(rig, chin, P)[1];
  rig.face.jaw.drop = 7;
  expect(offset(rig, chin, P)[1]).toBeCloseTo(2 * before, 5);
});

test('parallax and jaw drop are validated when present', () => {
  const rig = structuredClone(fixture);
  Object.assign(rig.head, { parallax: 0 }); Object.assign(rig.face.jaw, { drop: -2 });
  expect(validateRig(rig)).toEqual(expect.arrayContaining(['rig.head.parallax: must be positive', 'rig.face.jaw.drop: must be positive']));
});
