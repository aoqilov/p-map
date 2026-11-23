import { projectOnSeg } from './geo';
import type { XY } from './projection';
import type { ParkData } from './types';

export interface Route {
  points: XY[];
  meters: number;
}

/** Graf bir marta quriladi, keyin har bir so'rov — Dijkstra (binary heap bilan) */
export function createRouter(graph: ParkData['graph']) {
  const n = graph.nodes.length;
  const adj: { to: number; w: number }[][] = graph.nodes.map(() => []);
  for (const [a, b, w] of graph.edges) {
    adj[a].push({ to: b, w });
    adj[b].push({ to: a, w });
  }

  /** Bir nechta boshlang'ich tugundan (har biri o'z boshlang'ich narxi bilan) eng qisqa yo'l */
  function dijkstra(sources: { node: number; cost: number }[], to: number) {
    const dist = new Float64Array(n).fill(Infinity);
    const prev = new Int32Array(n).fill(-1);
    const heap: [number, number][] = [];
    const push = (item: [number, number]) => {
      heap.push(item);
      let i = heap.length - 1;
      while (i > 0) {
        const p = (i - 1) >> 1;
        if (heap[p][0] <= heap[i][0]) break;
        [heap[p], heap[i]] = [heap[i], heap[p]];
        i = p;
      }
    };
    const pop = () => {
      const top = heap[0];
      const last = heap.pop()!;
      if (heap.length) {
        heap[0] = last;
        let i = 0;
        for (;;) {
          const l = 2 * i + 1, r = l + 1;
          let m = i;
          if (l < heap.length && heap[l][0] < heap[m][0]) m = l;
          if (r < heap.length && heap[r][0] < heap[m][0]) m = r;
          if (m === i) break;
          [heap[m], heap[i]] = [heap[i], heap[m]];
          i = m;
        }
      }
      return top;
    };

    for (const s of sources) {
      if (s.cost < dist[s.node]) {
        dist[s.node] = s.cost;
        push([s.cost, s.node]);
      }
    }
    while (heap.length) {
      const [d, v] = pop();
      if (v === to) break;
      if (d > dist[v]) continue;
      for (const { to: w, w: len } of adj[v]) {
        const nd = d + len;
        if (nd < dist[w]) {
          dist[w] = nd;
          prev[w] = v;
          push([nd, w]);
        }
      }
    }
    if (!Number.isFinite(dist[to])) return null;
    const nodes: number[] = [];
    for (let v = to; v !== -1; v = prev[v]) nodes.push(v);
    nodes.reverse();
    return { nodes, meters: dist[to] };
  }

  /** Grafdagi eng yaqin yo'l bo'lagi va undagi nuqta (foydalanuvchini yo'lga "yopishtirish") */
  function snapToNetwork(p: XY) {
    let best = { edge: -1, t: 0, q: p as XY, d: Infinity };
    graph.edges.forEach(([a, b], i) => {
      const r = projectOnSeg(p, graph.nodes[a], graph.nodes[b]);
      if (r.d < best.d) best = { edge: i, t: r.t, q: r.q, d: r.d };
    });
    return best;
  }

  return {
    snapToNetwork,

    /** Tugundan tugungacha */
    between(from: number, to: number): Route | null {
      const r = dijkstra([{ node: from, cost: 0 }], to);
      return r && { points: r.nodes.map((i) => graph.nodes[i]), meters: r.meters };
    },

    /** Ixtiyoriy nuqtadan (masalan, GPS) tugungacha: avval eng yaqin yo'lga chiqadi */
    fromPoint(p: XY, to: number): Route | null {
      const s = snapToNetwork(p);
      if (s.edge < 0) return null;
      const [a, b, len] = graph.edges[s.edge];
      const r = dijkstra([{ node: a, cost: s.t * len }, { node: b, cost: (1 - s.t) * len }], to);
      if (!r) return null;
      return { points: [p, s.q, ...r.nodes.map((i) => graph.nodes[i])], meters: r.meters + s.d };
    },
  };
}
