import { expect, test } from 'vitest';
import fixture from '../samples/miko-qipao/rig.json';
import { parseRig, PARAMS, validateRig } from 'mesh-avatar';
import { createRig } from '../packages/runtime/src/engine/rig.js';

const phys = { gain: 0, bunL: [0, 0], bunR: [0, 0], strands: [] };
const pose = (extra: Record<string, number>) => ({ ...Object.fromEntries(PARAMS.map(p => [p.id, p.def])), ...extra });

// Two visible brows on one row, centred on the brow ellipse.
function twoBrowRig(extra: Record<string, unknown> = {}) {
  const rig = parseRig(fixture);
  rig.face.brow = { cx: 600, cy: 330, rx: 200, ry: 25, band: [350, 360], ...extra };
  return rig;
}
function dy(rig: ReturnType<typeof parseRig>, x: number, P: ReturnType<typeof pose>) {
  const R = createRig(rig), out = [0, 0];
  R.deformBase(x, 330, R.baseWeights(x, 330, 0), P, phys, out);
  return out[1] - 330;
}

test('a brow pair tilts mirrored: a positive angle lowers both inner ends', () => {
  const rig = twoBrowRig({ pair: [500, 700] });
  const P = pose({ browAngle: 1 });
  const leftInner = dy(rig, 540, P), rightInner = dy(rig, 660, P);
  const leftOuter = dy(rig, 460, P), rightOuter = dy(rig, 740, P);
  expect(leftInner).toBeGreaterThan(leftOuter);
  expect(rightInner).toBeGreaterThan(rightOuter);
  expect(leftInner).toBeCloseTo(rightInner, 5);
  expect(leftOuter).toBeCloseTo(rightOuter, 5);
});

test('without a pair the brow keeps its single-centre tilt', () => {
  const rig = twoBrowRig();
  const P = pose({ browAngle: 1 });
  expect(dy(rig, 540, P)).toBeLessThan(0);
  expect(dy(rig, 660, P)).toBeGreaterThan(0);
});

test('brow lift and tilt scale the movement', () => {
  const P = pose({ browY: 1 });
  expect(dy(twoBrowRig({ lift: 14 }), 600, P)).toBeCloseTo(2 * dy(twoBrowRig(), 600, P), 5);
  const tilted = pose({ browAngle: 1 });
  expect(Math.abs(dy(twoBrowRig({ tilt: 0.24 }), 700, tilted))).toBeGreaterThan(Math.abs(dy(twoBrowRig(), 700, tilted)));
});

test('brow pair, lift and tilt are validated when present', () => {
  const rig = structuredClone(fixture);
  Object.assign(rig.face.brow, { pair: [700, 500], lift: -1, tilt: 0 });
  const errors = validateRig(rig);
  expect(errors).toContain('rig.face.brow.pair: start must be less than end');
  expect(errors).toContain('rig.face.brow.lift: must be positive');
  expect(errors).toContain('rig.face.brow.tilt: must be positive');
});
