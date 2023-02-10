'''Test wal eval logic'''
import unittest
import math
from unittest.mock import patch
from io import StringIO

from wal.core import Wal
from wal.ast_defs import Symbol as S
from wal.ast_defs import Operator

# pylint: disable=C0103
# pylint: disable=W0201


class OpTest(unittest.TestCase):
    '''Test built-in functions'''

    def setUp(self):
        self.w = Wal()
        self.w.eval_context.environment.define('x', 5)
        self.w.eval_context.environment.define('y', 10)
        self.w.eval_context.environment.define('z', 0)

    @property
    def x(self):  # pylint: disable=C0116
        return self.w.eval_context.environment.read('x')
    
    @property
    def y(self):  # pylint: disable=C0116
        return self.w.eval_context.environment.read('y')

    @property
    def z(self):  # pylint: disable=C0116
        return self.w.eval_context.environment.read('z')

    def checkEqual(self, sexpr, res):
        '''eval first argument and check if result matches second argument '''
        self.assertEqual(self.w.eval(sexpr), res)


class BasicOpTest(OpTest):
    '''Test built-in functions'''

    def test_add(self):
        '''Test add evaluation'''

        # test int addition
        self.checkEqual('(+ 1 2)', 3)
        self.checkEqual('(+ x y)', self.x + self.y)
        self.checkEqual('(+ x 1)', self.x + 1)
        self.checkEqual('(+ x -1)', self.x + -1)
        # test mixed int string
        self.checkEqual('(+ x "hi")', f'{self.x}hi')
        # test string concatenation
        self.checkEqual('(+ "hi" "ho")', 'hiho')
        # test nested additions
        self.checkEqual('(+ (+ 1 1) (+ 2 2))', 6)
        # test single argument
        with self.assertRaises(AssertionError):
            self.w.eval('(+ 1)')

        # test list append
        self.checkEqual("(+ '(1 2) '(3 4))", [1, 2, 3, 4])
        self.checkEqual("(+ '(1 2) 3)", [1, 2, 3])

    def test_sub(self):
        '''Test sub evaluation'''

        # test int sub
        self.checkEqual('(- 5)', -5)
        self.checkEqual('(- 2 1)', 1)
        self.checkEqual('(- 1 2)', -1)
        self.checkEqual('(- y x)', self.y - self.x)
        # test mixed int string
        with self.assertRaises(AssertionError):
            self.w.eval('(- x 1 "test")')

        # test nested additions
        self.checkEqual('(- 10 (- 4 2))', 8)
        self.checkEqual('(- (- 10 10) (- 4 2))', -2)

    def test_mul(self):
        '''Test mul evaluation'''
        self.checkEqual('(* 2 2)', 4)
        self.checkEqual('(* x y)', self.x * self.y)
        self.checkEqual('(* x y z)', self.x * self.y * self.z)

    def test_div(self):
        '''Test mul evaluation'''
        self.checkEqual('(/ 22 2)', 11)
        self.checkEqual('(/ y x)', self.y / self.x)

        # we dont raise an exception but just print a warning
        # since this makes wal code significantly cleaner in some cases
        # with self.assertRaises(ZeroDivisionError):
        #     self.w.eval('(/ 5 0)')

        with self.assertRaises(AssertionError):
            self.w.eval('(/ 1)')

        with self.assertRaises(AssertionError):
            self.w.eval('(/ 1 "a")')

    def test_exp(self):
        '''Test exp evaluation'''
        self.checkEqual('(** 2 10)', 1024)
        self.checkEqual('(** x y)', math.pow(self.x, self.y))

        with self.assertRaises(AssertionError):
            self.w.eval('(** 1)')

        with self.assertRaises(AssertionError):
            self.w.eval('(** 1 "a")')

        with self.assertRaises(AssertionError):
            self.w.eval('(** 1 2 3)')

    def test_eq(self):
        '''Test eq operator'''
        self.checkEqual('(= 3 3)', 1)
        self.checkEqual('(= 3 3 3)', 1)
        self.checkEqual('(= "a" "a")', 1)
        self.checkEqual('(= 3 3 "a")', 0)
        self.checkEqual('(= x x)', 1)
        self.checkEqual('(= x y)', 0)
        self.checkEqual('(= (+ 2 2) (* 2 2))', 1)

    def test_neq(self):
        '''Test neq operator'''
        self.checkEqual('(!= 3 3)', 0)
        self.checkEqual('(!= 3 3 3)', 0)
        self.checkEqual('(!= "a" "a")', 0)
        self.checkEqual('(!= 3 3 "a")', 1)
        self.checkEqual('(!= x x)', 0)
        self.checkEqual('(!= x y)', 1)
        self.checkEqual('(!= (+ 2 2) (* 2 2))', 0)


    def test_larger(self):
        '''Test larger operator'''
        self.checkEqual('(> 1 0)', 1)
        self.checkEqual('(> 2 1)', 1)
        self.checkEqual('(> 1 -1)', 1)
        self.checkEqual('(> 0 0)', 0)
        self.checkEqual('(> -1 0)', 0)
        self.checkEqual('(> -2 -1)', 0)
        self.checkEqual('(> (+ 5 5) 5)', 1)
        self.checkEqual('(> x y)', 0)

        # compare only on two elements
        with self.assertRaises(AssertionError):
            self.w.eval("(> 3)")
        with self.assertRaises(AssertionError):
            self.w.eval("(> 3 4 5)")

        # compare only on ints
        with self.assertRaises(AssertionError):
            self.w.eval("(> '(1 2) 3)")
        with self.assertRaises(AssertionError):
            self.w.eval("(> '(1 2) '(3))")
        with self.assertRaises(AssertionError):
            self.w.eval("(> 3 '(3))")


    def test_smaller(self):
        '''Test smaller operator'''
        self.checkEqual('(< 1 0)', 0)
        self.checkEqual('(< 2 1)', 0)
        self.checkEqual('(< 1 -1)', 0)
        self.checkEqual('(< 0 0)', 0)
        self.checkEqual('(< -1 0)', 1)
        self.checkEqual('(< -2 -1)', 1)
        self.checkEqual('(< (+ 5 5) 5)', 0)
        self.checkEqual('(< x y)', 1)

        # compare only on two elements
        with self.assertRaises(AssertionError):
            self.w.eval("(< 3)")
        with self.assertRaises(AssertionError):
            self.w.eval("(< 3 4 5)")

        # compare only on ints
        with self.assertRaises(AssertionError):
            self.w.eval("(< '(1 2) 3)")
        with self.assertRaises(AssertionError):
            self.w.eval("(< '(1 2) '(3))")
        with self.assertRaises(AssertionError):
            self.w.eval("(< 3 '(3))")

    def test_larger_equal(self):
        '''Test larger equals operator'''
        self.checkEqual('(>= 1 0)', 1)
        self.checkEqual('(>= 2 1)', 1)
        self.checkEqual('(>= 1 -1)', 1)
        self.checkEqual('(>= 0 0)', 1)
        self.checkEqual('(>= -1 0)', 0)
        self.checkEqual('(>= -2 -1)', 0)
        self.checkEqual('(>= (+ 5 5) 5)', 1)
        self.checkEqual('(>= x y)', 0)

        # compare only on two elements
        with self.assertRaises(AssertionError):
            self.w.eval("(>= 3)")
        with self.assertRaises(AssertionError):
            self.w.eval("(>= 3 4 5)")

        # compare only on ints
        with self.assertRaises(AssertionError):
            self.w.eval("(>= '(1 2) 3)")
        with self.assertRaises(AssertionError):
            self.w.eval("(>= '(1 2) '(3))")
        with self.assertRaises(AssertionError):
            self.w.eval("(>= 3 '(3))")

    def test_smaller_equal(self):
        '''Test smaller equals operator'''
        self.checkEqual('(<= 1 0)', 0)
        self.checkEqual('(<= 2 1)', 0)
        self.checkEqual('(<= 1 -1)', 0)
        self.checkEqual('(<= 0 0)', 1)
        self.checkEqual('(<= -1 0)', 1)
        self.checkEqual('(<= -2 -1)', 1)
        self.checkEqual('(<= (+ 5 5) 5)', 0)
        self.checkEqual('(<= x y)', 1)

        # compare only on two elements
        with self.assertRaises(AssertionError):
            self.w.eval("(<= 3)")
        with self.assertRaises(AssertionError):
            self.w.eval("(<= 3 4 5)")

        # compare only on ints
        with self.assertRaises(AssertionError):
            self.w.eval("(<= '(1 2) 3)")
        with self.assertRaises(AssertionError):
            self.w.eval("(<= '(1 2) '(3))")
        with self.assertRaises(AssertionError):
            self.w.eval("(<= 3 '(3))")

    def test_and(self):
        '''Test logical and operator'''
        self.checkEqual('(&& 1 1)', True)
        self.checkEqual('(&& 1 1 2)', True)
        self.checkEqual('(&& 1 "a")', True)
        self.checkEqual("(&& 1 '(1 2 3))", True)
        self.checkEqual('(&& 1 0)', False)
        self.checkEqual('(&& 0 0)', False)

        with self.assertRaises(AssertionError):
            self.w.eval("(&&)")

    def test_or(self):
        '''Test logical and operator'''
        self.checkEqual('(|| 1 1)', True)
        self.checkEqual('(|| 1 1 2)', True)
        self.checkEqual('(|| 1 "a")', True)
        self.checkEqual("(|| 1 '(1 2 3))", True)
        self.checkEqual('(|| 1 0)', True)
        self.checkEqual('(|| 0 0)', False)

        with self.assertRaises(AssertionError):
            self.w.eval("(||)")

    def test_not(self):
        '''Test not operator'''
        self.checkEqual('(! 1)', 0)
        self.checkEqual('(! 0)', 1)

        with self.assertRaises(AssertionError):
            self.w.eval("(!)")

    def test_set(self):
        '''Test variable set function'''
        self.checkEqual('x', self.x)
        self.w.eval('(set (x 6))')
        self.checkEqual('x', 6)

        self.w.eval('(set (x (+ 1 2)))')
        self.checkEqual('x', 3)

        self.w.eval('(set (x (+ x x)))')
        self.checkEqual('x', 6)

        # check if set return correct value
        self.checkEqual('(set (x (+ x x)))', 12)

        self.w.eval('(set (a 11) (b 22))')
        self.checkEqual('a', 11)
        self.checkEqual('b', 22)

        self.checkEqual('(set (a 11) (b 22))', 22)

        # should fail because only symbols can be assigned to
        with self.assertRaises(AssertionError):
            self.w.eval('(set (5 5))')


class EvalPrintTest(OpTest):
    '''Test functions that produce output'''

    def test_print(self):
        '''Test simple print function'''
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.w.eval('(print "hello, world!")')
            self.assertEqual(fake_out.getvalue(), 'hello, world!\n')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.w.eval('(print "a" "bc")')
            self.assertEqual(fake_out.getvalue(), 'abc\n')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.w.eval('(print "a" "bc" 123)')
            self.assertEqual(fake_out.getvalue(), 'abc123\n')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.w.eval('(print)')
            self.assertEqual(fake_out.getvalue(), '\n')

    def test_printf(self):
        '''Test printf formated output'''
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.w.eval('(printf "hello, world!")')
            self.assertEqual(fake_out.getvalue(), 'hello, world!')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.w.eval('(printf "%s" "hello, world!")')
            self.assertEqual(fake_out.getvalue(), 'hello, world!')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.w.eval('(printf "%d" 15)')
            self.assertEqual(fake_out.getvalue(), '15')
            self.w.eval('(printf "%04d" 15)')
            self.assertEqual(fake_out.getvalue(), '150015')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.w.eval('(printf "%x" 15)')
            self.assertEqual(fake_out.getvalue(), 'f')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.w.eval('(printf "%x\\n" 15)')
            self.assertEqual(fake_out.getvalue(), 'f\n')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.w.eval('(printf "")')
            self.assertEqual(fake_out.getvalue(), '')

        with self.assertRaises(ValueError):
            self.w.eval('(printf 5 5)')


class EvalControlFlowTest(OpTest):
    '''Test control flow functions'''

    def test_if(self):
        '''Test if statements'''
        self.checkEqual('(if 1 2 3)', 2)
        self.checkEqual('(if 0 2 3)', 3)
        self.checkEqual('(if (> x y) 2 3)', 3)
        self.checkEqual('(if (! (> x y)) 2 3)', 2)
        self.checkEqual('(if 1 (+ 1 1) 3)', 2)
        self.checkEqual('(if 0 2 (+ 1 2))', 3)

        self.checkEqual('(if 1 2)', 2)
        self.checkEqual('(if 0 2)', None)

        with self.assertRaises(AssertionError):
            self.w.eval('(if)')
        with self.assertRaises(AssertionError):
            self.w.eval('(if 1)')

    def test_cond(self):
        '''Test conditional branches'''
        self.checkEqual('(cond (1 2) (2 3))', 2)
        self.checkEqual('(cond (0 2) (2 3))', 3)
        self.checkEqual('(cond (0 2) (0 3))', None)
        self.checkEqual('(cond ((= 1 1) 2) (2 3))', 2)
        self.checkEqual('(cond ((= 1 1) (+ 1 1)) (2 3))', 2)

        with self.assertRaises(AssertionError):
            self.w.eval('(cond)')

        with self.assertRaises(AssertionError):
            self.w.eval('(cond 1)')

        with self.assertRaises(AssertionError):
            self.w.eval('(cond (1))')

    def test_when(self):
        '''Test when construct'''
        self.checkEqual('(when 1 2)', 2)
        self.checkEqual('(when 0 2)', None)
        self.checkEqual('(when (= 1 1) 2)', 2)
        self.checkEqual('(when (= 1 0) 2)', None)
        self.checkEqual('(when (= 1 1) (+ 1 2))', 3)

        with self.assertRaises(AssertionError):
            self.w.eval('(when)')

        with self.assertRaises(AssertionError):
            self.w.eval('(when 1)')

    def test_unless(self):
        '''Test when construct'''
        self.checkEqual('(unless 1 2)', None)
        self.checkEqual('(unless 0 2)', 2)
        self.checkEqual('(unless (= 1 1) 2)', None)
        self.checkEqual('(unless (= 1 0) 2)', 2)
        self.checkEqual('(unless (= 1 1) (+ 1 2))', None)

        with self.assertRaises(AssertionError):
            self.w.eval('(unless)')

        with self.assertRaises(AssertionError):
            self.w.eval('(unless 1)')

    def test_case(self):
        '''Test case construct'''
        case1 = '(case a (1 "a") (2 "b") (3 "c"))'
        self.w.eval('(set (a 1))')
        self.checkEqual(case1, "a")
        self.w.eval('(set (a 2))')
        self.checkEqual(case1, "b")
        self.w.eval('(set (a 3))')
        self.checkEqual(case1, "c")

        self.w.eval('(set (a 4))')
        self.checkEqual(case1, None)

        # match complex data
        case2 = '(case a ("x" "a") ("y" "b") ("z" "c"))'
        self.w.eval('(set (a "x"))')
        self.checkEqual(case2, "a")

        case3 = '(case a ((1 1) "a") ((1 2) "b"))'
        self.w.eval("(set (a '(1 1)))")
        self.checkEqual(case3, "a")

        with self.assertRaises(ValueError):
            self.w.eval('(case 1 (1 a) (2 b) (1 c))')

        with self.assertRaises(AssertionError):
            self.w.eval('(case)')

    def test_do(self):
        '''Test sequential program execution'''
        self.checkEqual('(do 1 2)', 2)
        self.checkEqual('(do (+ 1 2) (+ 2 2))', 4)

        with self.assertRaises(AssertionError):
            self.w.eval('(do)')

    def test_while(self):
        '''Test while loop'''
        self.w.eval('(set (x 0))')
        self.checkEqual('(while (< x 5) (set (x (+ x 1))))', 5)

        # should fail since while expects 2 args
        with self.assertRaises(AssertionError):
            self.w.eval('(while (< x 5))')

    def test_alias(self):
        '''Test symbol renaming using aliases'''
        self.w.eval('(alias abc x)')
        self.checkEqual('abc', self.x)

        self.w.eval('(alias abc x def y)')
        self.checkEqual('def', self.y)

        # alias expects only an even number of arguments
        with self.assertRaises(AssertionError):
            self.w.eval('(alias)')

        with self.assertRaises(AssertionError):
            self.w.eval('(alias a 1 b)')

    def test_unalias(self):
        '''Test deleting aliases using unalias'''
        self.w.eval('(alias abc x)')
        self.checkEqual('abc', self.x)

        with self.assertRaises(AssertionError):
            self.w.eval('(unalias abc)')
            self.w.eval('abc')

        with self.assertRaises(AssertionError):
            self.w.eval('(unalias)')

        with self.assertRaises(AssertionError):
            self.w.eval('(unalias 1)')

        with self.assertRaises(AssertionError):
            self.w.eval('(unalias x y)')

    def test_quote(self):
        '''Test quoting'''
        self.checkEqual('(quote x)', S('x'))
        self.checkEqual("'x", S('x'))
        self.checkEqual("'(+ 1 2)", [Operator.ADD, 1, 2])

        with self.assertRaises(AssertionError):
            self.w.eval('(quote)')

        with self.assertRaises(AssertionError):
            self.w.eval('(quote a b)')

#     def test_inc(self):
#         '''Test incrementing'''
#         self.eval(Operator.SET, [S('x'), 1, S('y'), 2])
#         self.assertEqual(self.eval(Operator.INC, [S('x')]), 1 + 1)
#         self.assertEqual(self.se.eval({}, S('x')), 1 + 1)
#         self.assertEqual(self.eval(Operator.INC, [S('x'), S('y')]), 2 + 1)
#         self.assertEqual(self.eval(Operator.INC, [S('foobar')]), 1)

#         # should fail since inc requires at least 1 argument
#         with self.assertRaises(AssertionError):
#             self.eval(Operator.INC, [])
#         # should fail since inc arg must be symbols
#         with self.assertRaises(AssertionError):
#             self.eval(Operator.INC, [1])
#         # should fail since inc args must be initialized
#         # with self.assertRaises(AssertionError):
#         #    self.eval(Operator.INC, [S('foo')])
#         # should fail since dereferenced inc args must be ints
#         with self.assertRaises(AssertionError):
#             self.eval(Operator.SET, [S('foo'), 'bar'])
#             self.eval(Operator.INC, [S('foo')])


class EvalFunctionTest(OpTest):
    '''Test control flow functions'''

    def test_lambda_args(self):
        '''Lambdas should raise errors for wrong arguments'''
        with self.assertRaises(AssertionError):
            self.w.eval('(lambda (x))')

        with self.assertRaises(AssertionError):
            self.w.eval('(lambda (x 1) x)')

    def test_lambda_apply(self):
        '''Lambdas should perform correct action if applied'''

        # Apply from inline definition
        self.checkEqual('((lambda (x) (+ x 1)) 1)', 2)

        # correct number of args must be supplied
        with self.assertRaises(AssertionError):
            self.w.eval('(lambda (x) (+ x 1) 1 2)')

        # Apply named lambda
        self.w.eval('(set (foo (lambda (y) (* y 2))))')
        self.checkEqual('(foo 5)', 10)
