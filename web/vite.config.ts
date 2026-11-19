import fs from 'fs';
import path from 'path';
import {defineConfig} from 'vite';

export default defineConfig(() => {
  const websiteRoot = path.resolve(import.meta.dirname, 'website');
  return {
    base: './',
    root: websiteRoot,
    publicDir: false as const,
    build: {
      outDir: path.resolve(import.meta.dirname, 'dist'),
      emptyOutDir: true,
    },
    plugins: [
      {
        name: 'copy-static-website-files',
        apply: 'build' as const,
        closeBundle(error?: Error): void {
          if (error) {
            return;
          }
          const distDir = path.resolve(import.meta.dirname, 'dist');
          if (!fs.existsSync(distDir)) {
            return;
          }
          for (const entry of ['assets', 'style.css', 'script.js', 'sitemap.xml', 'robots.txt', '.nojekyll', 'CNAME']) {
            const srcPath = path.resolve(websiteRoot, entry);
            const destPath = path.resolve(distDir, entry);
            if (fs.existsSync(srcPath)) {
              fs.cpSync(srcPath, destPath, {recursive: true, force: true});
            }
          }
          // Ensure .nojekyll exists so GitHub Pages bypasses Jekyll
          fs.writeFileSync(path.resolve(distDir, '.nojekyll'), '');
        },
      },
    ],
    server: {
      hmr: process.env.DISABLE_HMR !== 'true',
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
    },
  };
});
