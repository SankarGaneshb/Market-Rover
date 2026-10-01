import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/investbrand/',
  define: {
    'process.env.PUBLIC_URL': JSON.stringify('/investbrand'),
    'process.env.REACT_APP_GOOGLE_CLIENT_ID': JSON.stringify('9514347926-lm36bs6ks9o6rl6bs5hac2cj9ptp9q4c.apps.googleusercontent.com')
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    emptyOutDir: true
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true
      }
    }
  }
});
