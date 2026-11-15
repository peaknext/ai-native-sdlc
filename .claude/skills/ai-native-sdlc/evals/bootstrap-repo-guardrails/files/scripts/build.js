'use strict';
const fs = require('node:fs');
const path = require('node:path');
const out = path.join(__dirname, '..', 'dist');
fs.rmSync(out, { recursive: true, force: true });
fs.cpSync(path.join(__dirname, '..', 'src'), out, { recursive: true });
console.log('Build succeeded');
