import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    manifest: true,
    rollupOptions: {
      output: {
        assetFileNames: 'assets/css/[name].css',
        entryFileNames: 'assets/js/[name].js',
      }
    }
  }
});
