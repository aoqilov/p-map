import { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import { colored, mergeAll } from './modelKit';

// Oqqush haykali: kulrang silindr poydevor, ustida oq to'lqinsimon qirqim, undan ikki oqqush (qanotlarini yoygan) chiqib turadi.
// Atrofida sakkiz burchakli gulzor (oq bordyur, yashil o'simliklar) va skameykalar.
export const SWAN_AT: [number, number] = [-76.8, 200.6];
const WHITE = '#f1efe8', WHITE2 = '#e3e1d8', GREY = '#8d949a';

const rg = (g: THREE.BufferGeometry, c: string) => colored(g, c);

function wing(side: 1 | -1, s: number, tilt: number) {
  const g: THREE.BufferGeometry[] = [];
  g.push(rg(new THREE.BoxGeometry(0.9, 0.22, 0.5).translate(0.45, 0, 0), WHITE)); // yelka
  for (let i = 0; i < 9; i++) {
    const L = 1.9 - Math.abs(i - 3) * 0.12 - i * 0.04, a = -0.25 + i * 0.12;
    g.push(rg(new THREE.BoxGeometry(L, 0.07, 0.2).translate(L / 2 + 0.7, 0, 0).rotateY(a), i % 2 ? WHITE2 : WHITE));
  }
  const m = mergeAll(g);
  m.scale(side * s, s, s); // x ni ko'zgulaydi; normal teskari bo'lmasligi uchun tomonlar ikki tomonlama material bilan chiziladi
  m.rotateZ(side * tilt);
  return m;
}

function swan(s: number, x: number, y: number, z: number, ry: number, wingTilt: number) {
  const g: THREE.BufferGeometry[] = [];
  g.push(rg(new THREE.SphereGeometry(0.55, 14, 10).scale(0.85, 0.7, 1.4).translate(0, 0.2, 0), WHITE));
  for (let i = 0; i <= 7; i++) {
    const t = i / 7;
    g.push(rg(new THREE.CylinderGeometry(0.2 - t * 0.07, 0.22 - t * 0.07, 0.34, 8).translate(0, 0.55 + t * 1.15, 0.38 - t * 0.15 + Math.sin(t * 3.14) * 0.05), WHITE));
  }
  g.push(rg(new THREE.SphereGeometry(0.15, 10, 8).scale(1, 1, 1.4).translate(0, 1.78, 0.2), WHITE));
  g.push(rg(new THREE.ConeGeometry(0.055, 0.24, 6).rotateX(Math.PI / 2).translate(0, 1.75, 0.43), '#e08a2a'));
  g.push(rg(new THREE.ConeGeometry(0.22, 0.6, 6).rotateX(-Math.PI / 2).translate(0, 0.3, -0.95), WHITE));
  g.push(wing(1, 1, wingTilt).translate(0.3, 1.15, -0.05), wing(-1, 1, wingTilt).translate(-0.3, 1.15, -0.05));
  const m = mergeAll(g);
  m.scale(s, s, s); m.rotateY(ry); m.translate(x, y, z);
  return m;
}

function build() {
  const g: THREE.BufferGeometry[] = [];
  // tosh yotqizilgan oval maydon
  g.push(rg(new THREE.CylinderGeometry(1, 1, 0.1, 48).scale(9.2, 1, 6.4).translate(0, 0.05, 0), '#8f7f72'));
  g.push(rg(new THREE.CylinderGeometry(1, 1, 0.03, 48).scale(9.0, 1, 6.2).translate(0, 0.115, 0), '#a89a8b'));
  // sakkiz burchakli gulzor: bordyur + yashil
  const N = 8, R = 3.9;
  g.push(rg(new THREE.CylinderGeometry(R * 0.98, R * 0.98, 0.12, N, 1).rotateY(Math.PI / N).translate(0, 0.19, 0), '#4f8a3a'));
  for (let i = 0; i < N; i++) {
    const a0 = ((i + 0.5) * Math.PI * 2) / N, a1 = ((i + 1.5) * Math.PI * 2) / N;
    const x0 = Math.cos(a0) * R, z0 = Math.sin(a0) * R, x1 = Math.cos(a1) * R, z1 = Math.sin(a1) * R;
    const len = Math.hypot(x1 - x0, z1 - z0);
    g.push(rg(new THREE.BoxGeometry(len + 0.1, 0.2, 0.22).rotateY(-Math.atan2(z1 - z0, x1 - x0)).translate((x0 + x1) / 2, 0.22, (z0 + z1) / 2), '#ddd9cf'));
  }
  // o'simliklar (shar-butalar)
  let sd = 5; const rnd = () => ((sd = (sd * 16807) % 2147483647) / 2147483647);
  const GR = ['#2f6e32', '#3f8a3a', '#6fa63a', '#a7c43a', '#2a5a2c'];
  for (let i = 0; i < 38; i++) {
    const a = rnd() * Math.PI * 2, r = 1.7 + rnd() * 2.0, sz = 0.18 + rnd() * 0.28;
    g.push(rg(new THREE.IcosahedronGeometry(sz, 0).scale(1.2, 0.85, 1.2).translate(Math.cos(a) * r, 0.25 + sz * 0.6, Math.sin(a) * r), GR[i % GR.length]));
  }
  // poydevor: kulrang silindr + oq to'lqinli bosh qism
  g.push(rg(new THREE.CylinderGeometry(1.15, 1.2, 1.3, 20).translate(0, 0.8, 0), GREY));
  g.push(rg(new THREE.CylinderGeometry(1.3, 1.15, 0.22, 20).translate(0, 1.55, 0), WHITE));
  for (let k = 0; k < 14; k++) {
    const a = (k / 14) * Math.PI * 2;
    g.push(rg(new THREE.TorusGeometry(0.22, 0.08, 6, 10, Math.PI * 1.5).rotateX(Math.PI / 2).translate(Math.cos(a) * 1.22, 1.5 + (k % 2) * 0.1, Math.sin(a) * 1.22), WHITE));
  }
  g.push(rg(new THREE.CylinderGeometry(1.0, 1.25, 0.3, 20).translate(0, 1.78, 0), WHITE2));
  // ikki oqqush: katta (qanotlari yoyiq) va uning orqasida kichikrog'i
  g.push(swan(0.85, 0.0, 1.9, 0.15, 0, 0.55), swan(0.62, -0.1, 1.9, -0.55, 0.15, 0.3));
  // skameykalar
  for (let k = 0; k < 4; k++) {
    const a = Math.PI / 4 + (k * Math.PI) / 2, x = Math.cos(a) * 7.4, z = Math.sin(a) * 5.2, ry = Math.atan2(-x / 7.4, -z / 5.2);
    const parts = [
      colored(new THREE.BoxGeometry(1.8, 0.06, 0.46).translate(0, 0.5, 0), '#a8703a'),
      colored(new THREE.BoxGeometry(1.8, 0.38, 0.04).translate(0, 0.82, -0.22), '#a8703a'),
      colored(new THREE.BoxGeometry(0.06, 0.5, 0.46).translate(-0.84, 0.25, 0), '#25282d'),
      colored(new THREE.BoxGeometry(0.06, 0.5, 0.46).translate(0.84, 0.25, 0), '#25282d'),
    ].map((p) => p.rotateY(ry).translate(x, 0.13, z));
    g.push(...parts);
  }
  return mergeAll(g);
}

export function SwanStatue() {
  const geo = useMemo(build, []);
  useEffect(() => () => geo.dispose(), [geo]);
  return (
    <group position={[SWAN_AT[0], 0, -SWAN_AT[1]]}>
      <mesh geometry={geo} castShadow receiveShadow><meshStandardMaterial vertexColors roughness={0.75} side={THREE.DoubleSide} /></mesh>
    </group>
  );
}
