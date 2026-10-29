export interface GroupRect { left: number; right: number; top: number; bottom: number }
interface Point { x: number; y: number }

/** Share rows while keeping each group's cells connected across a line break. */
export function placeLibraryGroups(counts: number[], columns: number) {
  let cursor = 0;
  return counts.map(count => {
    const start = cursor % columns;
    const remaining = columns - start;
    if (start && count > remaining && count - remaining <= start) cursor += remaining;
    return Array.from({ length: count }, () => {
      const cell = { column: cursor % columns + 1, row: Math.floor(cursor / columns) + 1 };
      cursor++;
      return cell;
    });
  });
}

function roundedPath(points: Point[], tabCorner: Point, radius: number) {
  const corners = points.filter((point, index, list) => {
    const before = list[(index + list.length - 1) % list.length];
    const after = list[(index + 1) % list.length];
    return (point.x - before.x) * (after.y - point.y) !== (point.y - before.y) * (after.x - point.x);
  }).map((point, index, list) => {
    const before = list[(index + list.length - 1) % list.length];
    const after = list[(index + 1) % list.length];
    const a = Math.hypot(point.x - before.x, point.y - before.y);
    const b = Math.hypot(after.x - point.x, after.y - point.y);
    const r = point.x === tabCorner.x && point.y === tabCorner.y ? 0 : Math.min(radius, a / 2, b / 2);
    return { point,
      enter: { x: point.x + (before.x - point.x) * r / a, y: point.y + (before.y - point.y) * r / a },
      exit: { x: point.x + (after.x - point.x) * r / b, y: point.y + (after.y - point.y) * r / b } };
  });
  if (!corners.length) return '';
  return `M ${corners[0].enter.x} ${corners[0].enter.y}` + corners.map(({ point, enter, exit }) =>
    ` L ${enter.x} ${enter.y} Q ${point.x} ${point.y} ${exit.x} ${exit.y}`).join('') + ' Z';
}

/** Outline the union of row runs and their vertical bridges, including concave corners. */
export function libraryGroupOutline(runs: GroupRect[], radius = 10) {
  if (!runs.length) return '';
  const rectangles = [...runs];
  for (let index = 1; index < runs.length; index++) {
    const a = runs[index - 1], b = runs[index];
    const left = Math.max(a.left, b.left), right = Math.min(a.right, b.right);
    if (right > left) rectangles.push({ left, right, top: a.bottom, bottom: b.top });
  }
  const xs = [...new Set(rectangles.flatMap(rect => [rect.left, rect.right]))].sort((a, b) => a - b);
  const ys = [...new Set(rectangles.flatMap(rect => [rect.top, rect.bottom]))].sort((a, b) => a - b);
  const filled = new Set<string>();
  for (let x = 0; x < xs.length - 1; x++) for (let y = 0; y < ys.length - 1; y++) {
    const cx = (xs[x] + xs[x + 1]) / 2, cy = (ys[y] + ys[y + 1]) / 2;
    if (rectangles.some(rect => cx > rect.left && cx < rect.right && cy > rect.top && cy < rect.bottom)) filled.add(`${x},${y}`);
  }
  const edges = new Map<string, string>();
  const edge = (x: number, y: number, nx: number, ny: number) => edges.set(`${x},${y}`, `${nx},${ny}`);
  for (const cell of filled) {
    const [x, y] = cell.split(',').map(Number);
    if (!filled.has(`${x},${y - 1}`)) edge(x, y, x + 1, y);
    if (!filled.has(`${x + 1},${y}`)) edge(x + 1, y, x + 1, y + 1);
    if (!filled.has(`${x},${y + 1}`)) edge(x + 1, y + 1, x, y + 1);
    if (!filled.has(`${x - 1},${y}`)) edge(x, y + 1, x, y);
  }
  const paths: string[] = [];
  while (edges.size) {
    const start = edges.keys().next().value!;
    let key = start;
    const points: Point[] = [];
    do {
      const [x, y] = key.split(',').map(Number);
      points.push({ x: xs[x], y: ys[y] });
      const next = edges.get(key);
      edges.delete(key);
      if (!next) break;
      key = next;
    } while (key !== start);
    paths.push(roundedPath(points, { x: runs[0].left, y: runs[0].top }, radius));
  }
  return paths.join(' ');
}
