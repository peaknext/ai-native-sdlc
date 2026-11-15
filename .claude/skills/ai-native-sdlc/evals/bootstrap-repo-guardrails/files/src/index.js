'use strict';

const { quote } = require('./pricing');

if (require.main === module) {
  const [price, qty] = process.argv.slice(2).map(Number);
  console.log(JSON.stringify(quote(price || 1000, qty || 1)));
}

module.exports = { quote };
