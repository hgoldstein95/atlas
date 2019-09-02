import unittest

from atlas import generator
from atlas.exceptions import ExceptionAsContinue
from atlas.strategies import DfsStrategy, operator
from atlas.utils.stubs import stub


@stub
def Select(*args, **kwargs):
    pass


@stub
def SelectReversed(*args, **kwargs):
    pass


class TestBasicGeneratorFunctionality(unittest.TestCase):
    def test_gen_single_1(self):
        @generator(strategy='dfs')
        def binary(length: int):
            s = ""
            for i in range(length):
                s += Select(["0", "1"])

            return s

        self.assertEqual(list(binary.generate(2)), ["00", "01", "10", "11"])

    def test_gen_custom_strategy_1(self):
        class ReversedDFS(DfsStrategy):
            def Select_reversed(self, domain, *args, **kwargs):
                yield from reversed(domain)

        @generator(strategy=ReversedDFS())
        def binary(length: int):
            s = ""
            for i in range(length):
                s += Select(["0", "1"], label='reversed')

            return s

        self.assertEqual(list(binary.generate(2)), list(reversed(["00", "01", "10", "11"])))

    def test_gen_custom_strategy_2(self):
        class ReversedDFS(DfsStrategy):
            @operator
            def SelectReversed(self, domain, *args, **kwargs):
                yield from reversed(domain)

        @generator(strategy=ReversedDFS())
        def binary(length: int):
            s = ""
            for i in range(length):
                s += SelectReversed(["0", "1"])

            return s

        self.assertEqual(list(binary.generate(2)), list(reversed(["00", "01", "10", "11"])))

    def test_gen_single_call_1(self):
        @generator(strategy='randomized')
        def binary(length: int):
            s = ""
            for i in range(length):
                s += Select(["0", "1"])

            return s

        self.assertIn(binary.call(2), ["00", "01", "10", "11"])

    def test_gen_exception_as_continue(self):
        @generator(strategy='dfs')
        def binary(length: int):
            s = ""
            for i in range(length):
                s += Select(["0", "1"])

            if s == "10":
                raise ExceptionAsContinue

            return s

        self.assertEqual(list(binary.generate(2)), ["00", "01", "11"])

    def test_gen_recursive_1(self):
        @generator(strategy='dfs')
        def binary(length: int):
            if length == 0:
                return ""

            return Select(["0", "1"]) + binary(length - 1)

        self.assertEqual(list(binary.generate(2)), ["00", "01", "10", "11"])

    def test_gen_recursive_2(self):
        @generator(strategy='dfs', caching=True)
        def binary(length: int):
            if length == 0:
                return ""

            return binary(length - 1) + Select(["0", "1"])

        self.assertEqual(list(binary.generate(2)), ["00", "01", "10", "11"])

    def test_gen_recursive_3(self):
        """ The non tail-recursive nature tests generator-level caching"""
        @generator(strategy='dfs', caching=True)
        def binary(length: int):
            if length == 0:
                return ""

            dummy = binary
            return dummy(length - 1) + Select(["0", "1"])

        self.assertEqual(list(binary.generate(2)), ["00", "01", "10", "11"])

    def test_gen_recursive_4(self):
        @generator(strategy='dfs')
        def binary(length: int):
            if length == 0:
                return ""

            dummy = binary
            return Select(["0", "1"]) + dummy(length - 1)

        self.assertEqual(list(binary.generate(2)), ["00", "01", "10", "11"])

    def test_gen_mutually_recursive_1(self):
        @generator(strategy='dfs')
        def binary1(length: int):
            if length == 0:
                return ""

            return Select(["0", "1"]) + binary2(length - 1)

        @generator(strategy='dfs')
        def binary2(length: int):
            if length == 0:
                return ""

            return Select(["0", "1"]) + binary1(length - 1)

        self.assertEqual(list(binary1.generate(2)), ["00", "01", "10", "11"])
        self.assertEqual(list(binary2.generate(2)), ["00", "01", "10", "11"])

    def test_gen_mutually_recursive_2(self):
        @generator(strategy='dfs')
        def binary(length: int):
            if length == 0:
                return ""

            return Select(["0", "1"]) + binary(length - 1)

        @generator(strategy='dfs')
        def binary1(length: int):
            if length == 0:
                return ""

            return Select(["0", "1"]) + binary2(length - 1)

        @generator(strategy='dfs')
        def binary2(length: int):
            if length == 0:
                return ""

            return Select(["0", "1"]) + binary1(length - 1)

        for l in [2, 3]:
            self.assertEqual(list(binary.generate(l)), list(binary1.generate(l)))
            self.assertEqual(list(binary.generate(l)), list(binary2.generate(l)))

    def test_gen_composition_1(self):
        @generator(group='binary')
        def lower_bit():
            return Select(["0", "1"])

        @generator(group='binary')
        def upper_bit():
            return Select(["0", "1"]) + lower_bit()

        self.assertEqual(list(upper_bit.generate()), ["00", "01", "10", "11"])

    def test_gen_composition_2(self):
        @generator(group='binary')
        def upper_bit():
            return Select(["0", "1"]) + lower_bit()

        @generator(group='binary')
        def lower_bit():
            return Select(["0", "1"])

        self.assertEqual(list(upper_bit.generate()), ["00", "01", "10", "11"])

    def test_gen_composition_without_groups_1(self):
        @generator
        def lower_bit():
            return Select(["0", "1"])

        @generator
        def upper_bit():
            return Select(["0", "1"]) + lower_bit()

        self.assertEqual(list(upper_bit.generate()), ["00", "01", "10", "11"])

    def test_gen_hooks_basic_1(self):
        @generator(strategy='dfs')
        def binary(length: int):
            s = ""
            for i in range(length):
                s += Select(["0", "1"])

            return s

        self.assertEqual([i[0] for i in list(binary.generate(2).with_tracing())], ["00", "01", "10", "11"])

    def test_gen_replay_basic_1(self):
        @generator(strategy='dfs')
        def binary(length: int):
            s = ""
            for i in range(length):
                s += Select(["0", "1"])

            return s

        traces = [i[1] for i in binary.generate(2).with_tracing()]

        self.assertEqual([list(binary.generate(2).replay(t))[0] for t in traces], ["00", "01", "10", "11"])

    def test_gen_replay_basic_2(self):
        @generator(strategy='dfs')
        def binary(length: int):
            s = ""
            for i in range(length):
                s += Select(["0", "1"])

            return s

        traces = [i[1] for i in binary.generate(2).with_tracing()]

        #  Arguments to generate omitted
        self.assertEqual([list(binary.generate().replay(t))[0] for t in traces], ["00", "01", "10", "11"])

    def test_gen_replay_with_labels(self):
        @generator(strategy='dfs')
        def binary(length: int):
            s = ""
            for i in range(length):
                s += Select(["0", "1"], label="bit_select")

            return s

        self.assertEqual(list(binary.generate(2).replay({"bit_select": ["0", "1"]}))[0], "01")


class TestGeneratorCompilation(unittest.TestCase):
    def test_arg_handling_1(self):
        @generator
        def binary(length: int, *args, **kwargs):
            s = ""
            for i in range(length):
                s += Select(["0", "1"])

            return s

        self.assertEqual(list(binary.generate(2, 'dummy')), ["00", "01", "10", "11"])