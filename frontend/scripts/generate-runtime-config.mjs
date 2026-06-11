import { mkdir, writeFile } from 'node:fs/promises';

const apiUrl = (process.env.API_URL || 'http://127.0.0.1:8000/api').replace(/\/+$/, '');
const output = `window.__CAREPOINT_CONFIG__ = ${JSON.stringify({ apiUrl })};\n`;

await mkdir(new URL('../public/', import.meta.url), { recursive: true });
await writeFile(new URL('../public/runtime-config.js', import.meta.url), output, 'utf8');
console.log(`CarePoint API configured as ${apiUrl}`);
