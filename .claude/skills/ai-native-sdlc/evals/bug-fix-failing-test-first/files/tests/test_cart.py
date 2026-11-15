import unittest

from shop.cart import Cart


class CartTests(unittest.TestCase):
    def test_empty_cart_is_zero(self):
        self.assertEqual(Cart().total(), 0)

    def test_total_without_discount(self):
        cart = Cart()
        cart.add("mug", 1200, 2)
        cart.add("poster", 800)
        self.assertEqual(cart.total(), 3200)

    def test_discount_on_single_item(self):
        cart = Cart()
        cart.add("mug", 1000)
        cart.apply_discount("WELCOME10")
        self.assertEqual(cart.total(), 900)

    def test_unknown_code_is_rejected(self):
        with self.assertRaises(ValueError):
            Cart().apply_discount("NOPE")


if __name__ == "__main__":
    unittest.main()
