import pred_check.PredicateExpression as PExp
import pred_check.PredicateMatcher as PMatch
import pred_check.PredicateTokenizer as PTk
import prop_check.PropositionalExpression as PropExp

_parse = PExp.PredicateExpression.parse


class PredicateProof:
    def __init__(self, goal):
        if isinstance(goal, str):
            goal = _parse(goal)
        self.goal = goal
        self.steps = []

    @staticmethod
    def parse_eq_rhs_reason(tokens):
        if tokens[0].type not in ['EQ', 'IMPLIEDBY']:
            raise ValueError("Expected a '=' or '-|' , but found : " + PTk.PredicateTokenizer.stringify_tokens(tokens))
        tokens = tokens[1:]
        rhs, tokens = PExp.PredicateExpression.parse_expression(tokens)
        if len(tokens) == 0:
            raise ValueError("Expected a '{', but found EOF")
        if tokens[0].type != 'LBRACE':
            raise ValueError("Expected a '{', but found : " + PTk.PredicateTokenizer.stringify_tokens(tokens))
        tokens = tokens[1:]
        if tokens[0].type == 'VAR' and tokens[0].value in ["rename", "migrate", "remove", "propositional"]:
            if tokens[0].value == 'rename':
                tokens = tokens[1:]
                x = PredicateProof.expect_variable(tokens)
                tokens = tokens[1:]
                PredicateProof.expect_keyword(tokens, 'to')
                tokens = tokens[1:]
                y = PredicateProof.expect_variable(tokens)
                tokens = tokens[1:]
                reason = ('rename', x, y)
            elif tokens[0].value in ['migrate', 'remove']:
                keyword = tokens[0].value
                tokens = tokens[1:]
                reason = (keyword, PredicateProof.expect_variable(tokens))
                tokens = tokens[1:]
            else:
                tokens = tokens[1:]
                PredicateProof.expect_keyword(tokens, 'reasoning')
                reason = ["propositional"]
                tokens = tokens[1:]
        else:
            raise ValueError("Expected a logical step (rename, migrate, remove, or propositional reasoning), " +
                             "but found: " + PTk.PredicateTokenizer.stringify_tokens(tokens))
        if len(tokens) == 0:
            raise ValueError("Expected a '}', but found EOF")
        if tokens[0].type != 'RBRACE':
            raise ValueError("Expected a '}', but found : " + PTk.PredicateTokenizer.stringify_tokens(tokens))
        tokens = tokens[1:]
        return rhs, reason, tokens

    @staticmethod
    def expect_keyword(tokens, keyword):
        if len(tokens) == 0:
            raise ValueError("Expected '" + keyword + "', but found EOF")
        if not (tokens[0].type == 'VAR' and tokens[0].value == keyword):
            raise ValueError("Expected '" + keyword + "', but found : " +
                             PTk.PredicateTokenizer.stringify_tokens(tokens))

    @staticmethod
    def expect_variable(tokens):
        if len(tokens) == 0:
            raise ValueError("Expected a variable, but found EOF")
        if tokens[0].type != 'VAR':
            raise ValueError("Expected a variable, but found : " +
                             PTk.PredicateTokenizer.stringify_tokens(tokens))
        return PExp.VariableExpression(tokens[0].value)

    @staticmethod
    def parse_proof_script(script):
        tokenizer = PTk.PredicateProofTokenizer()
        tokens = tokenizer.tokenize(script)
        expr, tokens = PExp.PredicateExpression.parse_expression(tokens)
        steps = [(expr, None)]
        while len(tokens) > 0:
            expr, name, tokens = PredicateProof.parse_eq_rhs_reason(tokens)
            steps.append((expr, name))
        return steps

    def check_proof(self, script=None):
        if script is not None:
            if isinstance(script, str):
                self.steps = PredicateProof.parse_proof_script(script)
            else:
                self.steps = script
        errors = []
        if len(self.steps) == 0:
            errors.append("Proof is empty")
            return errors
        if not self.steps[0][0].equal(self.goal):
            errors.append("Step 1: First step does not match the theorem you want to prove")
        for i in range(1, len(self.steps)):
            error_msg = None
            if self.steps[i - 1][0].equal(self.steps[i][0]):
                errors.append("Step {} does nothing".format(i + 1))
            elif self.steps[i][1][0] == 'rename':
                old_var = self.steps[i][1][1]
                new_var = self.steps[i][1][2]
                error_msg = PredicateProof.check_rename(old_var, new_var, self.steps[i - 1][0], self.steps[i][0])
            elif self.steps[i][1][0] == 'migrate':
                error_msg, _ = PredicateProof.check_migrate(self.steps[i][1][1], self.steps[i - 1][0], self.steps[i][0])
            elif self.steps[i][1][0] == 'remove':
                error_msg = PredicateProof.check_remove(self.steps[i][1][1], self.steps[i - 1][0], self.steps[i][0])
            else:
                error_msg, _ = PredicateProof.check_propositional(self.steps[i - 1][0], self.steps[i][0])
            if error_msg and error_msg is not True:
                errors.append("Step {}: {}".format(i + 1, error_msg))
        if not self.steps[-1][0].equal(PExp.LogicalConstantExpression(True)):
            errors.append("Step {}: Last step should always be 'True'".format(len(self.steps)))
        return errors

    @staticmethod
    def check_rename(old_var, new_var, lhs, rhs):
        if old_var.equal(new_var):
            return "A variable can only be renamed to a different name"
        return PredicateProof.check_rename_step(old_var, new_var, lhs, rhs)

    @staticmethod
    def check_rename_step(old_var, new_var, lhs, rhs, diff=False):
        if lhs.equal(rhs):
            return None
        if not isinstance(lhs, type(rhs)):
            return "Result does not match prior step by renaming variables"
        if isinstance(lhs, PExp.QuantifierExpression):
            if lhs.var.equal(old_var) and rhs.var.equal(new_var):
                if diff:
                    return "Takes more than one step at a time"
                if lhs.contains(new_var):
                    return "A variable can only be renamed to a new variable name, not an existing variable name"
                expected_rhs = lhs.expr.replace({lhs.var.value: rhs.var})
                if expected_rhs.equal(rhs.expr):
                    return True
                return "Result does not match prior step by renaming variables"
        for lhs_i, rhs_i in zip(lhs.children(), rhs.children()):
            error_msg = PredicateProof.check_rename_step(old_var, new_var, lhs_i, rhs_i, diff)
            if error_msg and error_msg is not True:
                return error_msg
        return True

    @staticmethod
    def check_migrate(old_var, lhs, rhs, diff=False):
        if lhs.equal(rhs):
            return None, diff
        if not lhs.has_unique_vars():
            return "Cannot migrate quantifiers until all quantified variables are uniquely renamed", diff
        if isinstance(rhs, PExp.QuantifierExpression) and rhs.var.equal(old_var):
            lhs, rhs = rhs, lhs
        if isinstance(lhs, PExp.QuantifierExpression) and lhs.var.equal(old_var):
            if isinstance(rhs, PExp.QuantifierExpression):
                if lhs.var.equal(rhs.var):
                    return PredicateProof.check_migrate(old_var, lhs.expr, rhs.expr, diff)
                if diff:
                    return "Takes more than one step at a time", True
                if not isinstance(rhs, type(lhs)):
                    return "Cannot migrate a quantifier past a different quantifier", True
                lhs1 = lhs.expr
                rhs1 = rhs.expr
                if not (isinstance(lhs1, type(lhs)) and isinstance(rhs1, type(lhs)) and
                        lhs1.var.equal(rhs.var) and rhs1.var.equal(lhs.var)):
                    return "Result does not match prior step by migrating quantifier", True
                return PredicateProof.check_migrate(old_var, lhs1.expr, rhs1.expr, True)
            elif isinstance(rhs, PExp.NotExpression):
                lhs1 = lhs.expr
                rhs1 = rhs.expr
                if not (isinstance(lhs1, PExp.NotExpression) and isinstance(rhs1, PExp.QuantifierExpression)):
                    return "Result does not match prior step by migrating quantifier", True
                if isinstance(rhs1, type(lhs)):
                    return "Migrating quantifier past negation should flip quantifier", True
                return PredicateProof.check_migrate(old_var, lhs1.expr, rhs1.expr, True)
            elif isinstance(rhs, PExp.BinaryExpression):
                lhs1 = lhs.expr
                rhs1a = rhs.lhs
                rhs1b = rhs.rhs
                if not isinstance(lhs1, type(rhs)):
                    return "Result does not match prior step by migrating quantifier", True
                if isinstance(rhs1a, PExp.QuantifierExpression) and rhs1a.var.equal(lhs.var):
                    if isinstance(rhs1a, type(lhs)):
                        if isinstance(rhs, PExp.ImpliesExpression):
                            return "Migrating quantifier past hypothesis of implication should flip quantifier", True
                    else:
                        if not isinstance(rhs, PExp.ImpliesExpression):
                            return "Migrating quantifier past logical connective should not flip quantifier", True
                    error_msg, diff = PredicateProof.check_migrate(old_var, lhs1.lhs, rhs1a.expr, True)
                    if error_msg and error_msg is not True:
                        return error_msg, True
                    return PredicateProof.check_migrate(old_var, lhs1.rhs, rhs1b, True)
                elif isinstance(rhs1b, PExp.QuantifierExpression) and rhs1b.var.equal(lhs.var):
                    if not isinstance(rhs1b, type(lhs)):
                        return "Migrating quantifier past logical connective should not flip quantifier", True
                    error_msg, diff = PredicateProof.check_migrate(old_var, lhs1.rhs, rhs1b.expr, True)
                    if error_msg and error_msg is not True:
                        return error_msg
                    return PredicateProof.check_migrate(old_var, lhs1.lhs, rhs1a, True)
            else:
                return "Result does not match prior step by migrating quantifier", True
        if not isinstance(rhs, type(lhs)):
            return "Result does not match prior step by migrating quantifier", diff
        for lhs_i, rhs_i in zip(lhs.children(), rhs.children()):
            error_msg, diff = PredicateProof.check_migrate(old_var, lhs_i, rhs_i, diff)
            if error_msg and error_msg is not True:
                return error_msg, diff
        return True, diff

    @staticmethod
    def check_remove(old_var, lhs, rhs):
        if not (isinstance(lhs, PExp.QuantifierExpression) and lhs.var.equal(old_var)):
            return "Only the quantifier at the very front can be removed"
        matcher = PMatch.PredicateMatcher()  # {lhs.var.value: lhs.var})
        if not matcher.match(lhs.expr, rhs):
            return "Resulting expression does not match prior expression after removing quantifier"
        for var_name, value in matcher.bindings.items():
            if var_name != old_var.value:
                if not (isinstance(value, PExp.VariableExpression) and value.value == var_name):
                    return "Resulting expression takes more than one quantifier removal step"
        if isinstance(lhs, PExp.ForallExpression):
            if old_var.value in matcher.bindings:
                new_value = matcher.bindings[old_var.value]
                if not isinstance(new_value, PExp.VariableExpression):
                    return "Variable in a forall can only be replaced by an unknown constant, like 'x0'"
                if old_var.value != new_value.value and lhs.expr.contains(new_value):
                    return "Variable in a forall can only be replaced by a totally new (constant) symbol"
        return True

    @staticmethod
    def check_propositional(lhs, rhs, diff=False):
        if not isinstance(rhs, type(lhs)):
            return PredicateProof.is_tautology(lhs, rhs), True
        if isinstance(lhs, PExp.PredicateInstanceExpression):
            if lhs.equal(rhs):
                return None, diff
            return "Resulting expression is not propositionally equivalent to prior step, e.g. when\n" + \
                   lhs.to_string() + " is True and " + rhs.to_string() + " is False", \
                   diff
        if isinstance(lhs, PExp.LogicalConstantExpression):
            if lhs.equal(rhs):
                return None, diff
            return "Resulting expression is not propositionally equivalent to prior since constant True is not False", \
                   diff
        if isinstance(lhs, PExp.QuantifierExpression):
            if not lhs.var.equal(rhs.var):
                return "Resulting expression is not propositionally equivalent to prior " + \
                       "since quantifiers with different variables are never propositionally equivalent", \
                       diff
            return PredicateProof.check_propositional(lhs.expr, rhs.expr, diff)
        for lhs_i, rhs_i in zip(lhs.children(), rhs.children()):
            error_msg, diff = PredicateProof.check_propositional(lhs_i, rhs_i, diff)
            if error_msg and error_msg is not True:
                return error_msg, diff
        return None, diff

    @staticmethod
    def is_tautology(lhs, rhs):
        pred_to_prop = {}
        prop_to_pred = {}
        lhs_prop = PredicateProof.convert_to_prop(lhs, pred_to_prop, prop_to_pred)
        rhs_prop = PredicateProof.convert_to_prop(rhs, pred_to_prop, prop_to_pred)
        prop = PropExp.IffExpression(lhs_prop, rhs_prop)
        bindings = {}
        return PredicateProof._is_tautology(prop, prop_to_pred, list(prop_to_pred.keys()), bindings)

    @staticmethod
    def convert_to_prop(expr, pred_to_prop, prop_to_pred):
        if isinstance(expr, PExp.NotExpression):
            child = PredicateProof.convert_to_prop(expr.expr, pred_to_prop, prop_to_pred)
            return PropExp.NotExpression(child)
        if isinstance(expr, PExp.BinaryExpression):
            child1 = PredicateProof.convert_to_prop(expr.lhs, pred_to_prop, prop_to_pred)
            child2 = PredicateProof.convert_to_prop(expr.rhs, pred_to_prop, prop_to_pred)
            if isinstance(expr, PExp.AndExpression):
                return PropExp.AndExpression(child1, child2)
            if isinstance(expr, PExp.OrExpression):
                return PropExp.OrExpression(child1, child2)
            if isinstance(expr, PExp.ImpliesExpression):
                return PropExp.ImpliesExpression(child1, child2)
            if isinstance(expr, PExp.IffExpression):
                return PropExp.IffExpression(child1, child2)
            raise ValueError("Internal Error: Unknown Binary Expression: " + str(expr))
        if isinstance(expr, PExp.LogicalConstantExpression):
            return PropExp.ConstantExpression(expr.value)
        pred = expr.to_string()
        if pred not in pred_to_prop:
            n = len(prop_to_pred.keys())
            prop = PropExp.VariableExpression("p" + str(n))
            pred_to_prop[pred] = prop
            prop_to_pred["p" + str(n)] = pred
        return pred_to_prop[pred]

    @staticmethod
    def _is_tautology(prop, prop_to_pred, var_names, bindings):
        if len(var_names) == 0:
            if prop.eval(bindings):
                return True
            return PredicateProof.create_error_msg_for_bindings(bindings, prop_to_pred)
        bindings[var_names[0]] = True
        error_msg = PredicateProof._is_tautology(prop, prop_to_pred, var_names[1:], bindings)
        if error_msg and error_msg is not True:
            return error_msg
        bindings[var_names[0]] = False
        return PredicateProof._is_tautology(prop, prop_to_pred, var_names[1:], bindings)

    @staticmethod
    def create_error_msg_for_bindings(bindings, prop_to_pred):
        error_msg = "Resulting expression is not propositionally equivalent to prior step, e.g. when"
        for var, value in bindings.items():
            error_msg += "\n" + prop_to_pred[var] + " is " + str(bindings[var])
        return error_msg

# proof_script = """
#    ((all x) P(x)) ==> ((exists x) P(x))
#  = ((all x) P(x)) ==> ((exists y) P(y))     { rename x to y }
#  = (exists x) [P(x) ==> ((exists y) P(y))]  { migrate x }
#  = (exists x) (exists y) [P(x) ==> P(y)]    { migrate y }
# -| (exists y) [P(0) ==> P(y)]               { remove x }
# -| P(0) ==> P(0)                            { remove y }
#  = True                                     { propositional reasoning }
# """
# proof_script1 = """
#    ((all x) P(x, y)) ==> ((exists x) P(x, y))
#  = ((all y) P(y, y)) ==> ((exists x) P(x, y))     { rename x to y }
#  = (exists x) [P(x) ==> ((exists y) P(y))]  { migrate x }
#  = (exists x) (exists y) [P(x) ==> P(y)]    { migrate y }
# -| (exists y) [P(0) ==> P(y)]               { remove x }
# -| P(0) ==> P(0)                            { remove y }
#  = True                                     { propositional reasoning }
# """
# proof_script2 = """
#    ((all x) P(x)) ==> ((all x) P(x))
#  = ((all x) P(x)) ==> ((all y) P(y))        { rename x to y }
#  = (all y) [(all x)P(x) ==> P(y)]           { migrate y }
#  = (all y) (exists x) [P(x) ==> P(y)]       { migrate x }
# -| (exists x) [P(x) ==> P(0)]               { remove y }
# -| P(0) ==> P(0)                            { remove x }
#  = True                                     { propositional reasoning }
# """
# proof_script3 = """
#    ((all x) P(x)) ==> ((all x) P(x))
#  = ((all x) P(x)) ==> ((all y) P(y))        { rename x to y }
#  = (all y) [(all x)P(x) ==> P(y)]           { migrate y }
#  = (all y) (exists x) [P(x) ==> P(y)]       { migrate x }
# -| (exists x) [P(x) ==> P(y0)]              { remove y }
# -| P(y0) ==> P(y0)                          { remove x }
#  = True                                     { propositional reasoning }
# """
# proof_script4 = """
#    ((all x) P(x)) ==> ((all x) P(x))
#  = ((all x) P(x)) ==> ((all y) P(y))        { rename x to y }
#  = (all y) [(all x)P(x) ==> P(y)]           { migrate y }
#  = (all y) (exists x) [P(x) ==> P(y)]       { migrate x }
#  = (exists x) (all y) [P(x) ==> P(y)]       { migrate x }
# -| (exists x) [P(x) ==> P(y0)]              { remove y }
# -| P(y0) ==> P(y0)                          { remove x }
#  = True                                     { propositional reasoning }
# """
# proof_script4 = """
#    ((all x) P(x)) ==> ~((all x) (P(x) \\/ Q(y)))
#  = ((all x) P(x)) ==> ~((all y) (P(y) \\/ Q(y)))        { rename x to y }
#  = ((all x) P(x)) ==> (exists y) ~(P(y) \\/ Q(y))        { migrate y }
# """
# proof_script5 = """
#    P(x) /\\ Q(x) ==> P(x) \\/ Q(x)
#  = P(x) \\/ ~P(x)       { propositional reasoning }
# """
# proof_script6 = """
#    (all x)P(x) ==> P(0) /\\ P(1)
#  = [(all x)P(x) /\\ (all x)P(x)] ==> P(0) /\\ P(1)       { propositional reasoning }
#  = [(all x)P(x) /\\ (all y)P(y)] ==> P(0) /\\ P(1)       { rename x to y }
#  = (all x)[P(x) /\\ (all y)P(y)] ==> P(0) /\\ P(1)       { migrate x }
#  = (all x, y)[P(x) /\\ P(y)] ==> P(0) /\\ P(1)           { migrate y }
#  = (some x)[(all y)[P(x) /\\ P(y)] ==> P(0) /\\ P(1)]    { migrate x }
#  = (some x, y)[P(x) /\\ P(y) ==> P(0) /\\ P(1)]          { migrate y }
#  = (some y)[P(0) /\\ P(y) ==> P(0) /\\ P(1)]             { remove x }
#  = P(0) /\\ P(1) ==> P(0) /\\ P(1)                       { remove y }
#  = True                                                  { propositional reasoning }
# """
#
# proof = PredicateProof("(all x)P(x) ==> P(0) /\\ P(1)")
# errors0 = proof.check_proof(proof_script6)
# print(errors0)
