import { StrictMode, Suspense, lazy, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import ParkMap from './ParkMap';
import type { MapMode } from './map/config';
import './styles.css';

// Bu fayl faqat shu loyihani alohida ishga tushirish va sinash uchun.
// O'z loyihangizda: mini-app'da <ParkMap mode="miniapp" />, adminkada <ParkMap mode="admin" />.
// Sinov: manzil oxiriga #admin qo'shsangiz — adminka rejimi.
const readMode = (): MapMode => (window.location.hash === '#admin' ? 'admin' : 'miniapp');
const isTestBuild = import.meta.env.DEV || import.meta.env.MODE === 'demo';

/** #editor — 2D setka tahrirlagich (faqat dev / demo): bino joyi va o'lchamini o'zgartirib, matn qilib olish */
const GridEditor = lazy(() => import('./editor/GridEditor'));

function Root() {
  const [mode, setMode] = useState(readMode);
  const [editor, setEditor] = useState(() => window.location.hash === '#editor');
  useEffect(() => {
    const onHash = () => { setMode(readMode()); setEditor(window.location.hash === '#editor'); };
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  if (editor && isTestBuild) return <Suspense fallback={null}><GridEditor /></Suspense>;
  return <ParkMap key={mode} mode={mode} features={isTestBuild ? { simulation: true } : undefined} />;
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
