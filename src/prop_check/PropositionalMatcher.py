class PropositionalMatcher:
    def __init__(self):
        self.bindings = {}

    def reset(self):
        self.bindings = {}

    def match(self, pattern, expr):
        return pattern.match(expr, self.bindings)

    def replace(self, pattern):
        return pattern.replace(self.bindings)


# pattern0 = PExp.PropositionalExpression.parse("x /\\ y ==> x")
# replace = PExp.PropositionalExpression.parse("~(x /\\ y) \\/ x")
# expr0 = PExp.PropositionalExpression.parse("(p <=> q) /\\ ~~r ==> (p <=> q)")
#
# print(pattern0)
# print(replace)
# print(expr0)
# matcher = PropositionalMatcher()
# print(matcher.match(pattern0, expr0))
# print(matcher.bindings)
# print(matcher.replace(replace))
