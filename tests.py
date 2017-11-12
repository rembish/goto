from unittest.case import TestCase

from goto import goto


class DecoratorTestCase(TestCase):
    @goto
    def test_goto(self):
        n = 10

        label .label1
        n -= 1
        if n != 0:
            goto .label1
        else:
            goto .label2

        label .label2
        self.assertEqual(n, 0)
