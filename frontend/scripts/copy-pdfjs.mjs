// Copies the PDF.js assets the in-app reader loads at runtime (fonts for PDFs
// without embedded fonts, character maps, wasm image decoders) into public/pdfjs.
// Runs on `npm install` (postinstall); public/pdfjs is git-ignored.
import { cpSync, rmSync } from 'node:fs'

const from = 'node_modules/pdfjs-dist'
const to = 'public/pdfjs'
rmSync(to, { recursive: true, force: true })
for (const dir of ['cmaps', 'standard_fonts', 'wasm']) {
  cpSync(`${from}/${dir}`, `${to}/${dir}`, { recursive: true })
}
console.log(`Copied PDF.js assets to ${to}`)
