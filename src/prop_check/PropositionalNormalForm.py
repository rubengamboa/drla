import prop_check.PropositionalExpression as PExp

class PropositionalNormalForm:
    @staticmethod
    def convert_to_negation_normal_form(expr):
        expr1 = expr.simplify()
        if isinstance(expr1, PExp.AndExpression):
            return PExp.AndExpression(PropositionalNormalForm.convert_to_negation_normal_form(expr1.lhs),
                                      PropositionalNormalForm.convert_to_negation_normal_form(expr1.rhs))
        elif isinstance(expr1, PExp.OrExpression):
            return PExp.OrExpression(PropositionalNormalForm.convert_to_negation_normal_form(expr1.lhs),
                                      PropositionalNormalForm.convert_to_negation_normal_form(expr1.rhs))
        elif isinstance(expr1, PExp.ImpliesExpression):
            return PExp.OrExpression(PropositionalNormalForm.convert_to_negation_normal_form(
                                        PExp.NotExpression(expr1.lhs)),
                                     PropositionalNormalForm.convert_to_negation_normal_form(expr1.rhs))
        elif isinstance(expr1, PExp.IffExpression):
            return PExp.OrExpression(
                        PExp.AndExpression(PropositionalNormalForm.convert_to_negation_normal_form(expr1.lhs),
                                           PropositionalNormalForm.convert_to_negation_normal_form(expr1.rhs)),
                        PExp.AndExpression(PropositionalNormalForm.convert_to_negation_normal_form(
                                                PExp.NotExpression(expr1.lhs)),
                                           PropositionalNormalForm.convert_to_negation_normal_form(
                                                PExp.NotExpression(expr1.rhs))))
        elif isinstance(expr1, PExp.NotExpression):
            expr2 = expr1.expr
            if isinstance(expr2, PExp.NotExpression):
                return PropositionalNormalForm.convert_to_negation_normal_form(expr2.expr)
            elif isinstance(expr2, PExp.AndExpression):
                return PExp.OrExpression(PropositionalNormalForm.convert_to_negation_normal_form(
                                            PExp.NotExpression(expr2.lhs)),
                                         PropositionalNormalForm.convert_to_negation_normal_form(
                                            PExp.NotExpression(expr2.rhs)))
            elif isinstance(expr2, PExp.OrExpression):
                return PExp.AndExpression(PropositionalNormalForm.convert_to_negation_normal_form(
                                            PExp.NotExpression(expr2.lhs)),
                                          PropositionalNormalForm.convert_to_negation_normal_form(
                                            PExp.NotExpression(expr2.rhs)))
            elif isinstance(expr2, PExp.ImpliesExpression):
                return PExp.AndExpression(PropositionalNormalForm.convert_to_negation_normal_form(expr2.lhs),
                                          PropositionalNormalForm.convert_to_negation_normal_form(
                                              PExp.NotExpression(expr2.rhs)))
            elif isinstance(expr2, PExp.IffExpression):
                return PExp.OrExpression(
                            PExp.AndExpression(PropositionalNormalForm.convert_to_negation_normal_form(expr2.lhs),
                                               PropositionalNormalForm.convert_to_negation_normal_form(
                                                    PExp.NotExpression(expr2.rhs))),
                            PExp.AndExpression(PropositionalNormalForm.convert_to_negation_normal_form(
                                                    PExp.NotExpression(expr2.lhs)),
                                               PropositionalNormalForm.convert_to_negation_normal_form(expr2.rhs)))
        return expr1

    @staticmethod
    def push_and_into_or(expr):
        if isinstance(expr, PExp.AndExpression):
            expr1 = expr.lhs
            expr2 = expr.rhs
            if isinstance(expr2, PExp.OrExpression):
                return PExp.OrExpression(PropositionalNormalForm.push_and_into_or(
                                            PExp.AndExpression(expr1, expr2.lhs)),
                                         PropositionalNormalForm.push_and_into_or(
                                            PExp.AndExpression(expr1, expr2.rhs)))
            elif isinstance(expr1, PExp.OrExpression):
                return PExp.OrExpression(PropositionalNormalForm.push_and_into_or(
                    PExp.AndExpression(expr1.lhs, expr2)),
                    PropositionalNormalForm.push_and_into_or(
                        PExp.AndExpression(expr1.rhs, expr2)))
        return expr

    @staticmethod
    def convert_negation_to_disjunctive_normal_form(expr):
        if isinstance(expr, PExp.AndExpression):
            expr1 = PropositionalNormalForm.convert_negation_to_disjunctive_normal_form(expr.lhs)
            expr2 = PropositionalNormalForm.convert_negation_to_disjunctive_normal_form(expr.rhs)
            return PropositionalNormalForm.push_and_into_or(PExp.AndExpression(expr1, expr2))
        elif isinstance(expr, PExp.OrExpression):
            expr1 = PropositionalNormalForm.convert_negation_to_disjunctive_normal_form(expr.lhs)
            expr2 = PropositionalNormalForm.convert_negation_to_disjunctive_normal_form(expr.rhs)
            return PExp.OrExpression(expr1, expr2)
        return expr



# expr1 = PExp.PropositionalExpression.parse("(p <=> q) <=> ~(r ==> s)")
# s1 = expr1.to_string()
# print(s1)
# expr2 = PropositionalNormalForm.convert_to_negation_normal_form(expr1)
# s2 = expr2.to_string()
# print(s2)

expr1 = PExp.PropositionalExpression.parse("(p \\/ q /\\ r) /\\ (~p \\/ ~r)")
s1 = expr1.to_string()
print(s1)
expr2 = PropositionalNormalForm.convert_to_negation_normal_form(expr1)
s2 = expr2.to_string()
print(s2)
expr3 = PropositionalNormalForm.convert_negation_to_disjunctive_normal_form(expr2)
s3 = expr3.to_string()
print(s3)
