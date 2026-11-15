'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { quote } = require('../src/pricing');

test('quote adds tax to the subtotal', () => {
  assert.deepStrictEqual(quote(1000, 2), { subtotal: 2000, tax: 140, total: 2140 });
});

test('quote rejects a zero quantity', () => {
  assert.throws(() => quote(1000, 0), RangeError);
});
