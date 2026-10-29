import { expect, it } from 'vitest';
import { libraryGroupOutline, placeLibraryGroups } from './libraryGroupLayout';

it('wraps a large group and fills its remaining row with smaller groups', () => {
  const [large, medium, single] = placeLibraryGroups([6, 3, 1], 5);
  expect(large).toEqual([
    { column: 1, row: 1 }, { column: 2, row: 1 }, { column: 3, row: 1 },
    { column: 4, row: 1 }, { column: 5, row: 1 }, { column: 1, row: 2 },
  ]);
  expect(medium).toEqual([{ column: 2, row: 2 }, { column: 3, row: 2 }, { column: 4, row: 2 }]);
  expect(single).toEqual([{ column: 5, row: 2 }]);
});

it('starts a new row when wrapping would disconnect a group outline', () => {
  const [, next] = placeLibraryGroups([2, 3], 4);
  expect(next).toEqual([{ column: 1, row: 2 }, { column: 2, row: 2 }, { column: 3, row: 2 }]);
  expect(placeLibraryGroups([2, 1], 1)).toEqual([
    [{ column: 1, row: 1 }, { column: 1, row: 2 }], [{ column: 1, row: 3 }],
  ]);
});

it('joins unequal row runs into one closed outline with a concave turn', () => {
  const path = libraryGroupOutline([
    { left: 0, top: 0, right: 500, bottom: 150 },
    { left: 0, top: 190, right: 100, bottom: 340 },
  ], 0);
  expect(path.match(/M /g)).toHaveLength(1);
  expect(path).toContain('500 150');
  expect(path).toContain('100 150');
  expect(path).toContain('100 340');
  expect(path.endsWith(' Z')).toBe(true);
  expect(libraryGroupOutline([])).toBe('');
});
