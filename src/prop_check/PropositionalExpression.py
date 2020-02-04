import prop_check.PropositionalTokenizer as PTk


class PropositionalExpression:
    def __repr__(self):
        return str(self)

    @staticmethod
    def parse(s):
        tokenizer = PTk.PropositionalTokenizer()
        expr, rest = PropositionalExpression.parse_expression(tokenizer.tokenize(s))
        if len(rest) != 0:
            raise ValueError("Expected END but found tokens: " + PTk.PropositionalTokenizer.stringify_tokens(rest))
        return expr

    @staticmethod
    def parse_expression(tokens):
        lhs, rest = PropositionalExpression.parse_implication(tokens)
        if len(rest) == 0:
            expr = lhs
        else:
            expr = lhs
            if rest[0].type == 'IFF':
                expr, rest = PropositionalExpression.parse_expression(rest[1:])
                expr = IffExpression(lhs, expr)
        return expr, rest

    @staticmethod
    def parse_implication(tokens):
        lhs, rest = PropositionalExpression.parse_disjunction(tokens)
        if len(rest) == 0:
            expr = lhs
        else:
            expr = lhs
            if rest[0].type == 'IMPLIES':
                expr, rest = PropositionalExpression.parse_implication(rest[1:])
                expr = ImpliesExpression(lhs, expr)
        return expr, rest

    @staticmethod
    def parse_disjunction(tokens):
        lhs, rest = PropositionalExpression.parse_conjunction(tokens)
        if len(rest) == 0:
            expr = lhs
        else:
            expr = lhs
            if rest[0].type == 'OR':
                expr, rest = PropositionalExpression.parse_disjunction(rest[1:])
                expr = OrExpression(lhs, expr)
        return expr, rest

    @staticmethod
    def parse_conjunction(tokens):
        lhs, rest = PropositionalExpression.parse_negation(tokens)
        if len(rest) == 0:
            expr = lhs
        else:
            expr = lhs
            if rest[0].type == 'AND':
                expr, rest = PropositionalExpression.parse_conjunction(rest[1:])
                expr = AndExpression(lhs, expr)
        return expr, rest

    @staticmethod
    def parse_negation(tokens):
        if len(tokens) > 0 and tokens[0].type == 'NOT':
            rest = tokens
            while True:
                expr, rest = PropositionalExpression.parse_negation(rest[1:])
                expr = NotExpression(expr)
                if len(rest) == 0 or rest[0].type != 'NOT':
                    break
        else:
            expr, rest = PropositionalExpression.parse_atom(tokens)
        return expr, rest

    @staticmethod
    def parse_atom(tokens):
        if len(tokens) == 0:
            raise ValueError("Expected an atom, but found EOF")
        if tokens[0].type == 'LPAREN':
            expr, rest = PropositionalExpression.parse_expression(tokens[1:])
            if len(rest) == 0:
                raise ValueError("Expected a ')', but found EOF")
            if rest[0].type != 'RPAREN':
                raise ValueError("Expected a ')', but found : " + PTk.PropositionalTokenizer.stringify_tokens(rest))
            return expr, rest[1:]
        elif tokens[0].type == 'VAR':
            return VariableExpression(tokens[0].value), tokens[1:]
        elif tokens[0].type == 'PROP':
            return ConstantExpression(tokens[0].value), tokens[1:]
        else:
            raise ValueError("Expected a variable or constant, but found: " +
                             PTk.PropositionalTokenizer.stringify_tokens(tokens))


class ConstantExpression (PropositionalExpression):
    def __init__(self, value):
        self.value = value

    def eval(self, _bindings):
        return self.value

    def match(self, other, _bindings):
        return self.equal(other)

    def replace(self, _bindings):
        return self

    def equal(self, other):
        return isinstance(other, ConstantExpression) and self.value == other.value

    # noinspection PyMethodMayBeStatic
    def children(self):
        return []

    def __str__(self):
        return str(self.value)

    def to_string(self, _level=0):
        return str(self.value)


class VariableExpression (PropositionalExpression):
    def __init__(self, symbol):
        self.symbol = symbol

    def eval(self, bindings):
        return bindings[self.symbol]

    def match(self, other, bindings):
        if self.symbol in bindings:
            return bindings[self.symbol].equal(other)
        bindings[self.symbol] = other
        return True

    def replace(self, bindings):
        if self.symbol in bindings:
            return bindings[self.symbol]
        return self

    def equal(self, other):
        return isinstance(other, VariableExpression) and self.symbol == other.symbol

    # noinspection PyMethodMayBeStatic
    def children(self):
        return []

    def __str__(self):
        return self.symbol

    def to_string(self, _level=0):
        return self.symbol


class NotExpression (PropositionalExpression):
    def __init__(self, expr):
        self.expr = expr

    def eval(self, bindings):
        return not self.expr.eval(bindings)

    def match(self, other, bindings):
        return isinstance(other, NotExpression) and self.expr.match(other.expr, bindings)

    def replace(self, bindings):
        return NotExpression(self.expr.replace(bindings))

    def equal(self, other):
        return isinstance(other, NotExpression) and self.expr.equal(other.expr)

    def children(self):
        return [self.expr]

    def __str__(self):
        return "Not(" + str(self.expr) + ")"

    def to_string(self, level=0):
        left = self.expr.to_string(10)
        if level > 10:
            return "(~" + left + ")"
        else:
            return "~" + left


class BinaryExpression (PropositionalExpression):
    def __init__(self, opstr, op, level, lhs, rhs):
        self.opstr = opstr
        self.op = op
        self.level = level
        self.lhs = lhs
        self.rhs = rhs

    def match(self, expr, bindings):
        return isinstance(expr, type(self)) \
               and self.lhs.match(expr.lhs, bindings) \
               and self.rhs.match(expr.rhs, bindings)

    def replace(self, bindings):
        return (type(self))(self.lhs.replace(bindings), self.rhs.replace(bindings))

    def equal(self, other):
        return isinstance(other, type(self)) \
               and self.lhs.equal(other.lhs) \
               and self.rhs.equal(other.rhs)

    def children(self):
        return [self.lhs, self.rhs]

    def __str__(self):
        return self.opstr + "(" + str(self.lhs) + ", " + str(self.rhs) + ")"

    def to_string(self, level=0):
        left = self.lhs.to_string(self.level + 1)
        right = self.rhs.to_string(self.level)
        if level > self.level:
            return "(" + left + " " + self.op + " " + right + ")"
        else:
            return left + " " + self.op + " " + right


class AndExpression (BinaryExpression):
    def __init__(self, lhs, rhs):
        super().__init__("And", "/\\", 8, lhs, rhs)

    def eval(self, bindings):
        return self.lhs.eval(bindings) and self.rhs.eval(bindings)


class OrExpression (BinaryExpression):
    def __init__(self, lhs, rhs):
        super().__init__("Or", "\\/", 6, lhs, rhs)

    def eval(self, bindings):
        return self.lhs.eval(bindings) or self.rhs.eval(bindings)


class ImpliesExpression (BinaryExpression):
    def __init__(self, lhs, rhs):
        super().__init__("Implies", "==>", 4, lhs, rhs)

    def eval(self, bindings):
        return (not self.lhs.eval(bindings)) or self.rhs.eval(bindings)


class IffExpression (BinaryExpression):
    def __init__(self, lhs, rhs):
        super().__init__("Iff", "<=>", 2, lhs, rhs)

    def eval(self, bindings):
        if self.lhs.eval(bindings):
            return self.rhs.eval(bindings)
        else:
            return not self.rhs.eval(bindings)


# expr1 = PropositionalExpression.parse("(p ==> q <=> r /\\ s \\/ (t <=> ~(~u) /\\ v)) " +
#                                       "/\\ (p ==> q <=> r /\\ s \\/ (t <=> ~(~u) /\\ v))")
# print(expr1)
# s1 = expr1.to_string()
# print(s1)
# expr1 = PropositionalExpression.parse(s1)
# print(expr1.to_string())
#
#
# expr1 = PropositionalExpression.parse("p /\\ q /\\ r")
# print(expr1)
# s1 = expr1.to_string()
# print(s1)
# expr1 = PropositionalExpression.parse(s1)
# print(expr1.to_string())
