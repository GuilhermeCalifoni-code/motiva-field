import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// O eixo da rodovia mora em db/rodovias/ — é a tabela rodovias.eixo nascendo.
// O alias e o fs.allow deixam o web/ ler esse arquivo sem duplicá-lo aqui.
const raizRepositorio = fileURLToPath(new URL('..', import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@db': fileURLToPath(new URL('../db', import.meta.url)),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
    fs: {
      allow: [raizRepositorio],
    },
  },
})
