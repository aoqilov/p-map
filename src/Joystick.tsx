// Ekrandagi joystik (3-shaxs yurish rejimi): barmoq bilan surilgan yo'nalish → `value` ref ({ x: o'ngga, y: oldinga }, −1..1).
// Qo'yib yuborilganda markazga qaytadi. Ref orqali — har harakatda React qayta chizmaydi (mobil uchun yengil).
import { useRef, useState } from 'react';
import type { WalkInput } from './map/Walker';

const R = 46; // knob harakat radiusi, px

export function Joystick({ value, bottom }: { value: React.MutableRefObject<WalkInput>; bottom: number }) {
  const base = useRef<HTMLDivElement>(null);
  const knob = useRef<HTMLDivElement>(null);
  const active = useRef<number | null>(null);
  const [on, setOn] = useState(false);

  const update = (cx: number, cy: number) => {
    const r = base.current!.getBoundingClientRect();
    let dx = cx - (r.left + r.width / 2), dy = cy - (r.top + r.height / 2);
    const d = Math.hypot(dx, dy);
    if (d > R) { dx *= R / d; dy *= R / d; }
    knob.current!.style.transform = `translate(${dx}px, ${dy}px)`;
    value.current = { x: dx / R, y: -dy / R };
  };
  const release = () => {
    active.current = null;
    setOn(false);
    value.current = { x: 0, y: 0 };
    if (knob.current) knob.current.style.transform = 'translate(0px, 0px)';
  };

  return (
    <div
      ref={base}
      className={`joystick${on ? ' is-on' : ''}`}
      style={{ bottom }}
      role="application"
      aria-label="Yurish: barmoq bilan suring (kompyuterda — WASD yoki strelkalar)"
      onPointerDown={(e) => {
        e.preventDefault();
        e.stopPropagation();
        active.current = e.pointerId;
        (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
        setOn(true);
        update(e.clientX, e.clientY);
      }}
      onPointerMove={(e) => { if (active.current === e.pointerId) update(e.clientX, e.clientY); }}
      onPointerUp={(e) => { if (active.current === e.pointerId) release(); }}
      onPointerCancel={release}
      onLostPointerCapture={release}
    >
      <div ref={knob} className="joystick__knob" />
    </div>
  );
}
