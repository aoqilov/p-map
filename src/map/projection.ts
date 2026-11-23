// Lon/lat → park markaziga nisbatan metr (x = sharq, y = shimol).
// Nega: xom Mercator koordinatalari (~7.7 mln m) GPU float32 ga sig'maydi va sahna titraydi.
// 600 m hududda bu tekis proyeksiyaning xatosi sm darajasida.

export const ORIGIN = { lon: 69.29866, lat: 41.31233 } as const;

const KX = 111_320 * Math.cos((ORIGIN.lat * Math.PI) / 180);
const KY = 110_540;

export type XY = [number, number];

export const project = ([lon, lat]: number[]): XY => [(lon - ORIGIN.lon) * KX, (lat - ORIGIN.lat) * KY];

export const unproject = ([x, y]: XY): XY => [x / KX + ORIGIN.lon, y / KY + ORIGIN.lat];
