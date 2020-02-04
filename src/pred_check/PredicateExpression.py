import copy

import pred_check.PredicateTokenizer as PTk


class PredicateExpression:
    def __repr__(self):
        return str(self)

    @staticmethod
    def parse(s):
        tokenizer = PTk.PredicateTokenizer()
        expr, rest = PredicateExpression.parse_expression(tokenizer.tokenize(s))
        if len(rest) != 0:
            raise ValueError("Expected END but found tokens: " + PTk.PredicateTokenizer.stringify_tokens(rest))
        arities = {}
        expr.check_predicate_arities(arities)
        return expr

    @staticmethod
    def parse_literal(s):
        tokenizer = PTk.PredicateTokenizer()
        expr, rest = PredicateExpression.parse_var_or_const(tokenizer.tokenize(s))
        if len(rest) != 0:
            raise ValueError("Expected END but found tokens: " + PTk.PredicateTokenizer.stringify_tokens(rest))
        return expr

    @staticmethod
    def parse_expression(tokens):
        lhs, rest = PredicateExpression.parse_implication(tokens)
        if len(rest) == 0:
            expr = lhs
        else:
            expr = lhs
            if rest[0].type == 'IFF':
                expr, rest = PredicateExpression.parse_expression(rest[1:])
                expr = IffExpression(lhs, expr)
        return expr, rest

    @staticmethod
    def parse_implication(tokens):
        lhs, rest = PredicateExpression.parse_disjunction(tokens)
        if len(rest) == 0:
            expr = lhs
        else:
            expr = lhs
            if rest[0].type == 'IMPLIES':
                expr, rest = PredicateExpression.parse_implication(rest[1:])
                expr = ImpliesExpression(lhs, expr)
        return expr, rest

    @staticmethod
    def parse_disjunction(tokens):
        lhs, rest = PredicateExpression.parse_conjunction(tokens)
        if len(rest) == 0:
            expr = lhs
        else:
            expr = lhs
            if rest[0].type == 'OR':
                expr, rest = PredicateExpression.parse_disjunction(rest[1:])
                expr = OrExpression(lhs, expr)
        return expr, rest

    @staticmethod
    def parse_conjunction(tokens):
        lhs, rest = PredicateExpression.parse_negation(tokens)
        if len(rest) == 0:
            expr = lhs
        else:
            expr = lhs
            if rest[0].type == 'AND':
                expr, rest = PredicateExpression.parse_conjunction(rest[1:])
                expr = AndExpression(lhs, expr)
        return expr, rest

    @staticmethod
    def parse_negation(tokens):
        if len(tokens) > 0 and tokens[0].type == 'NOT':
            rest = tokens
            while True:
                expr, rest = PredicateExpression.parse_negation(rest[1:])
                expr = NotExpression(expr)
                if len(rest) == 0 or rest[0].type != 'NOT':
                    break
        else:
            expr, rest = PredicateExpression.parse_atom(tokens)
        return expr, rest

    @staticmethod
    def parse_atom(tokens):
        if len(tokens) == 0:
            raise ValueError("Expected an atom, but found EOF")
        if len(tokens) >= 2 and tokens[0].type == 'LPAREN' and tokens[1].type in ['ALL', 'EXISTS']:
            quantifier = tokens[1].type
            variables = []
            tokens = tokens[2:]
            while len(tokens) > 0:
                if tokens[0].type != 'VAR':
                    raise ValueError("Expected a variable, but found: " +
                                     PTk.PredicateTokenizer.stringify_tokens(tokens))
                variables.append(VariableExpression(tokens[0].value))
                tokens = tokens[1:]
                if len(tokens) == 0 or tokens[0].type == 'RPAREN':
                    break
                if tokens[0].type == 'COMMA':
                    tokens = tokens[1:]
            if len(tokens) == 0:
                raise ValueError("Expected a ',' variable or ')', but found EOF")
            tokens = tokens[1:]
            expr, rest = PredicateExpression.parse_negation(tokens)
            for var in reversed(variables):
                if quantifier == 'ALL':
                    expr = ForallExpression(var, expr)
                else:
                    expr = ExistsExpression(var, expr)
            return expr, rest
        elif tokens[0].type == 'LPAREN' or tokens[0].type == 'LBRACKET':
            right_delim = 'RPAREN' if tokens[0].type == 'LPAREN' else 'RBRACKET'
            expr, rest = PredicateExpression.parse_expression(tokens[1:])
            if len(rest) == 0:
                if right_delim == 'RPAREN':
                    raise ValueError("Expected a ')', but found EOF")
                else:
                    raise ValueError("Expected a ']', but found EOF")
            if rest[0].type != right_delim:
                if right_delim == 'RPAREN':
                    raise ValueError("Expected a ')', but found: " + PTk.PredicateTokenizer.stringify_tokens(rest))
                else:
                    raise ValueError("Expected a ']', but found: " + PTk.PredicateTokenizer.stringify_tokens(rest))
            return expr, rest[1:]
        elif tokens[0].type == 'VAR':
            pred = tokens[0].value
            args = []
            if len(tokens) == 0:
                raise ValueError("Expected a '(', but found EOF")
            tokens = tokens[1:]
            if tokens[0].type != 'LPAREN':
                raise ValueError("Expected a '(', but found: " + PTk.PredicateTokenizer.stringify_tokens(tokens))
            tokens = tokens[1:]
            while len(tokens) > 0:
                arg, tokens = PredicateExpression.parse_var_or_const(tokens)
                args.append(arg)
                if len(tokens) == 0 or tokens[0].type == 'RPAREN':
                    break
                if tokens[0].type != 'COMMA':
                    raise ValueError("Expected a ',' or ')', but found: " +
                                     PTk.PredicateTokenizer.stringify_tokens(tokens))
                tokens = tokens[1:]
            if len(tokens) == 0:
                raise ValueError("Expected a ',' or ')', but found EOF")
            return PredicateInstanceExpression(pred, args), tokens[1:]
        elif tokens[0].type == 'PROP':
            return LogicalConstantExpression(tokens[0].value), tokens[1:]
        else:
            raise ValueError("Expected a predicate or logical constant, but found: " +
                             PTk.PredicateTokenizer.stringify_tokens(tokens))

    @staticmethod
    def parse_var_or_const(tokens):
        if tokens[0].type == 'VAR':
            arg = VariableExpression(tokens[0].value)
        elif tokens[0].type == 'CONST':
            arg = NumericConstantExpression(tokens[0].value)
        else:
            raise ValueError("Expected a variable or constant, but found: " +
                             PTk.PredicateTokenizer.stringify_tokens(tokens))
        return arg, tokens[1:]

    def collect_vars(self):
        known_vars = set()
        self.collect_vars_helper(known_vars)

    def collect_vars_helper(self, known_vars):
        for child in self.children():
            child.collect_vars_helper(known_vars)

    def has_unique_vars(self):
        known_vars = set()
        return self.has_unique_vars_helper(known_vars)

    def has_unique_vars_helper(self, known_vars):
        for child in self.children():
            if not child.has_unique_vars_helper(known_vars):
                return False
        return True

    def contains(self, var):
        for child in self.children():
            if child.contains(var):
                return True
        return False

    def check_predicate_arities(self, arities):
        for child in self.children():
            child.check_predicate_arities(arities)

    # noinspection PyMethodMayBeStatic
    def children(self):
        return []


class ObjectExpression:
    def __init__(self, value):
        self.value = value

    def match(self, other, _bindings):
        return self.equal(other)

    def replace(self, _bindings):
        return self

    def equal(self, other):
        return isinstance(other, type(self)) and self.value == other.value

    def collect_vars_helper(self, known_vars):
        return

    # noinspection PyMethodMayBeStatic
    def has_unique_vars_helper(self, _known_vars):
        return True

    def contains(self, var):
        return False

    # noinspection PyMethodMayBeStatic
    def children(self):
        return []

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "<" + type(self).__name__ + ":" + str(self.value) + ">"

    def to_string(self, _level=0):
        return str(self.value)


class NumericConstantExpression(ObjectExpression):
    def __init__(self, value):
        super().__init__(value)


class VariableExpression(ObjectExpression):
    def __init__(self, symbol):
        super().__init__(symbol)

    def match(self, other, bindings):
        if self.value in bindings:
            return bindings[self.value].equal(other)
        bindings[self.value] = other
        return True

    def replace(self, bindings):
        if self.value in bindings:
            return bindings[self.value]
        return self

    def collect_vars_helper(self, known_vars):
        for var in known_vars:
            if self.equal(var):
                return
        known_vars.append(self)

    def contains(self, var):
        return self.equal(var)


class LogicalConstantExpression(PredicateExpression):
    def __init__(self, value):
        self.value = value

    def match(self, other, _bindings):
        return self.equal(other)

    def replace(self, _bindings):
        return self

    def equal(self, other):
        return isinstance(other, type(self)) and self.value == other.value

    # noinspection PyMethodMayBeStatic
    def children(self):
        return []

    def __str__(self):
        return str(self.value)

    def to_string(self, _level=0):
        return str(self.value)


class PredicateInstanceExpression(PredicateExpression):
    def __init__(self, predicate, args):
        self.predicate = predicate
        self.args = args

    def match(self, other, _bindings):
        if isinstance(other, type(self)) and self.predicate == other.predicate and len(self.args) == len(other.args):
            for i in range(len(self.args)):
                if not self.args[i].match(other.args[i], _bindings):
                    return False
            return True
        else:
            return False

    def replace(self, _bindings):
        new_args = []
        for arg in self.args:
            new_args.append(arg.replace(_bindings))
        return PredicateInstanceExpression(self.predicate, new_args)

    def equal(self, other):
        if isinstance(other, type(self)) and self.predicate == other.predicate and len(self.args) == len(other.args):
            for i in range(len(self.args)):
                if not self.args[i].equal(other.args[i]):
                    return False
            return True
        else:
            return False

    def children(self):
        return self.args

    def check_predicate_arities(self, arities):
        if self.predicate in arities:
            if len(self.args) != arities[self.predicate]:
                raise ValueError(f"Predicate {self.predicate} is used with different number of arguments " +
                                 f"({len(self.args)} vs {arities[self.predicate]})")
        else:
            arities[self.predicate] = len(self.args)

    def __str__(self):
        args = []
        for arg in self.args:
            args.append(str(arg))
        return self.predicate + "(" + ",".join(args) + ")"

    def to_string(self, _level=0):
        return str(self)


class QuantifierExpression(PredicateExpression):
    def __init__(self, quantifier, var, expr):
        self.quantifier = quantifier
        self.var = var
        self.expr = expr

    def match(self, other, bindings):
        if not isinstance(other, type(self)):
            return False
        if self.quantifier != other.quantifier:
            return False
        new_bindings = copy.deepcopy(bindings)
        new_bindings[self.var.value] = other.var
        return self.expr.match(other.expr, bindings)

    def replace(self, bindings):
        new_bindings = copy.deepcopy(bindings)
        new_bindings[self.var.value] = self.var
        return (type(self))(self.var, self.expr.replace(new_bindings))

    def equal(self, other):
        return isinstance(other, type(self)) and \
               self.quantifier == other.quantifier and \
               self.var.equal(other.var) and \
               self.expr.equal(other.expr)

    def has_unique_vars_helper(self, known_vars):
        if self.var.value in known_vars:
            return False
        known_vars.add(self.var.value)
        return True

    def check_predicate_arities(self, arities):
        self.expr.check_predicate_arities(arities)

    def children(self):
        return [self.var, self.expr]

    def __str__(self):
        return "(" + self.quantifier + " " + str(self.var) + ")" + "(" + str(self.expr) + ")"

    def to_string(self, level=0):
        prefix = "(" + self.quantifier + " " + str(self.var)
        expr = self.expr
        while isinstance(expr, type(self)) and self.quantifier == expr.quantifier:
            prefix += " " + str(expr.var)
            expr = expr.expr
        prefix += ")"
        left = expr.to_string(10)
        if left[0] != '(':
            left = " " + left
        if level > 10:
            return "(" + prefix + left + ")"
        else:
            return prefix + left


class ForallExpression(QuantifierExpression):
    def __init__(self, var, expr):
        super().__init__("all", var, expr)


class ExistsExpression(QuantifierExpression):
    def __init__(self, var, expr):
        super().__init__("some", var, expr)


class NotExpression(PredicateExpression):
    def __init__(self, expr):
        self.expr = expr

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


class BinaryExpression(PredicateExpression):
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


class AndExpression(BinaryExpression):
    def __init__(self, lhs, rhs):
        super().__init__("And", "/\\", 8, lhs, rhs)


class OrExpression(BinaryExpression):
    def __init__(self, lhs, rhs):
        super().__init__("Or", "\\/", 6, lhs, rhs)


class ImpliesExpression(BinaryExpression):
    def __init__(self, lhs, rhs):
        super().__init__("Implies", "==>", 4, lhs, rhs)


class IffExpression(BinaryExpression):
    def __init__(self, lhs, rhs):
        super().__init__("Iff", "<=>", 2, lhs, rhs)

# expr1 = PredicateExpression.parse("(forall x) (forall y) (exists z) P(x, y, z) ==> (exists w) Q(x, w, z)")
# print(expr1)
# s1 = expr1.to_string()
# print(s1)
# expr1 = PredicateExpression.parse(s1)
# print(expr1.to_string())
#
#
# expr1 = PredicateExpression.parse("(all x) (forall y) (some z) [P(x, y, z) ==> (exists w) ~Q(x, w, z) /\\ P(y)]")
# print(expr1)
# s1 = expr1.to_string()
# print(s1)
# expr1 = PredicateExpression.parse(s1)
# print(expr1.to_string())
