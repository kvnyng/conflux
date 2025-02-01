import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
    base: '/',
    server: {
        middlewareMode: false, // Ensure Vite is handling routes normally
        configureServer(server) {
            server.middlewares.use((req, res, next) => {
                if (!req.url.includes('.') && !req.url.endsWith('/')) {
                    req.url += '/';
                }
                next();
            });
        }
    },
    build: {
        rollupOptions: {
            input: {
                main: path.resolve(__dirname, 'index.html'),
                planets: path.resolve(__dirname, 'planets/index.html'),
                landscapes: path.resolve(__dirname, 'landscapes/index.html'),
                scan: path.resolve(__dirname, 'scan/index.html')
            }
        }
    },

});