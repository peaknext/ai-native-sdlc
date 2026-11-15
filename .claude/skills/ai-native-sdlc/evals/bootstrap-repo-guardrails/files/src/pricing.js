'use strict';

const TAX_RATE = 0.07;

function quote(unitPriceCents, quantity) {
  if (!Number.isInteger(quantity) || quantity < 1) {
    throw new RangeError('quantity must be a positive integer');
  }
  const subtotal = unitPriceCents * quantity;
  const tax = Math.round(subtotal * TAX_RATE);
  return { subtotal, tax, total: subtotal + tax };
}

module.exports = { quote, TAX_RATE };
