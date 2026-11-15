'use strict';
const target = process.argv[2];
if (!['staging', 'production'].includes(target)) {
  console.error('usage: deploy.js staging|production');
  process.exit(1);
}
console.log(`(pretend) deployed quote-service to ${target}`);
