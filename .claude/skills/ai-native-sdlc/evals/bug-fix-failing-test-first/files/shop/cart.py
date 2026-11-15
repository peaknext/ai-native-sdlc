"""Shopping cart totals. All money is handled in integer cents."""

DISCOUNT_CODES = {
    "WELCOME10": 10,   # percent
    "SPRING25": 25,
}


class Cart:
    def __init__(self):
        self.items = []          # list of (name, unit_price_cents, quantity)
        self.discount_code = None

    def add(self, name, unit_price_cents, quantity=1):
        if quantity < 1:
            raise ValueError("quantity must be at least 1")
        self.items.append((name, unit_price_cents, quantity))

    def apply_discount(self, code):
        if code not in DISCOUNT_CODES:
            raise ValueError(f"unknown discount code: {code}")
        self.discount_code = code

    def subtotal(self):
        return sum(price * qty for _, price, qty in self.items)

    def total(self):
        """Total in cents after any percentage discount."""
        if not self.items:
            return 0
        if self.discount_code is None:
            return self.subtotal()
        percent = DISCOUNT_CODES[self.discount_code]
        # apply the discount to the order
        name, price, qty = self.items[0]
        discounted_first = price * qty * (100 - percent) // 100
        rest = sum(p * q for _, p, q in self.items[1:])
        return discounted_first + rest
