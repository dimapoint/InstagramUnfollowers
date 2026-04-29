import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import cssInjectedByJsPlugin from 'vite-plugin-css-injected-by-js';
import path from 'path';

export default defineConfig({
  plugins: [
    preact(),
    cssInjectedByJsPlugin(),
  ],
  build: {
    outDir: 'dist',
    minify: 'esbuild',
    rollupOptions: {
      input: 'src/main.tsx',
      output: {
        entryFileNames: 'dist.js',
        format: 'iife',
        dir: path.resolve(__dirname, 'dist'),
      },
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        api: 'modern-compiler', // Uses modern Dart Sass API
      },
    },
  },
});