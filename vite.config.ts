import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { viteSingleFile } from 'vite-plugin-singlefile';

// `npm run build:demo` — hamma narsa bitta HTML faylga (demo ulashish uchun, sinov tugmalari bilan)
// `npm run build:client` — mijozga ko'rsatish uchun toza bitta HTML fayl (sinov tugmalarisiz, istalgan hostingga qo'yiladi)
const single = (mode: string) => mode === 'demo' || mode === 'client';

/** Faqat demo rejimida: ko'rish oynasi chetlarigacha cho'zilsin (demo sahifasi uchun maxsus meta) */
const demoMeta = (mode: string): Plugin => ({
  name: 'demo-meta',
  transformIndexHtml: (html) => (mode === 'demo'
    ? html.replace('</title>', '</title>\n    <meta name="claude:viewport-fit-sides" content="cover" />')
    : html),
});

export default defineConfig(({ mode }) => ({
  plugins: [react(), demoMeta(mode), ...(single(mode) ? [viteSingleFile()] : [])],
  build: single(mode)
    ? { outDir: mode === 'client' ? 'dist-client' : 'dist-demo', chunkSizeWarningLimit: 4000 }
    : { chunkSizeWarningLimit: 1500 },
}));
