# import pred_check.PredicateExpression as PExp


class PredicateMatcher:
    def __init__(self, bindings=None):
        if bindings is None:
            bindings = {}
        self.bindings = bindings

    def reset(self, bindings=None):
        if bindings is None:
            bindings = {}
        self.bindings = bindings

    def match(self, pattern, expr):
        return pattern.match(expr, self.bindings)

    def replace(self, pattern):
        return pattern.replace(self.bindings)


# pattern0 = PExp.PredicateExpression.parse("(forall y) (some z) [P(x, y, z) ==> (exists w, x) ~Q(x, w, z) /\\ R(y)]")
# replace = PExp.PredicateExpression.parse("(forall w, y, z) P(w, x, y, z)")
# expr0 = PExp.PredicateExpression.parse("(forall a) (some z) [P(3, a, z) ==> (exists w, x) ~Q(x, w, z) /\\ R(y)]")
#
# print(pattern0)
# print(replace)
# print(expr0)
# matcher = PredicateMatcher()
# print(matcher.match(pattern0, expr0))
# print(matcher.bindings)
# print(matcher.replace(replace))
