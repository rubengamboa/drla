import prop_check.PropositionalExpression as PExp
import prop_check.PropositionalTokenizer as PTk
import prop_check.PropositionalMatcher as PMatch

_parse = PExp.PropositionalExpression.parse


_AXIOMS = {"\\/ identity": (_parse("x \\/ False"), _parse("x")),
           "\\/ null": (_parse("x \\/ True"), _parse("True")),
           "\\/ commutative": (_parse("x \\/ y"), _parse("y \\/ x")),
           "\\/ associative": (_parse("x \\/ (y \\/ z)"), _parse("(x \\/ y) \\/ z")),
           "\\/ distributive": (_parse("x \\/ (y /\\ z)"), _parse("(x \\/ y) /\\ (x \\/ z)")),
           "implication": (_parse("x ==> y"), _parse("(~x) \\/ y")),
           "\\/ demorgan": (_parse("~(x \\/ y)"), _parse("(~x) /\\ (~y)")),
           "\\/ idempotent": (_parse("x \\/ x"), _parse("x")),
           "self - implication": (_parse("x ==> x"), _parse("True")),
           "double negation": (_parse("~(~x)"), _parse("x"))
           }


class PropositionalProof:
    def __init__(self, lhs, rhs, extra_axioms=None):
        if isinstance(lhs, str):
            lhs = _parse(lhs)
        if isinstance(rhs, str):
            rhs = _parse(rhs)
        self.lhs = lhs
        self.rhs = rhs
        self.axioms = _AXIOMS
        if extra_axioms is not None:
            if isinstance(extra_axioms, str):
                extra_axioms = PropositionalProof.parse_extra_axioms(extra_axioms)
            self.axioms.update(extra_axioms)
        self.steps = []

    @staticmethod
    def parse_eq_rhs_reason(tokens):
        if tokens[0].type != 'EQ':
            raise ValueError("Expected a '=', but found : " + PTk.PropositionalTokenizer.stringify_tokens(tokens))
        tokens = tokens[1:]
        rhs, tokens = PExp.PropositionalExpression.parse_expression(tokens)
        if len(tokens) == 0:
            raise ValueError("Expected a '{', but found EOF")
        if tokens[0].type != 'LBRACE':
            raise ValueError("Expected a '{', but found : " + PTk.PropositionalTokenizer.stringify_tokens(tokens))
        tokens = tokens[1:]
        reason = []
        while len(tokens) > 0 and tokens[0].type != 'RBRACE':
            reason.append(tokens[0])
            tokens = tokens[1:]
        if len(tokens) == 0:
            raise ValueError("Expected a '}', but found EOF")
        tokens = tokens[1:]
        name = " ".join([str(token.value) for token in reason])
        return rhs, name, tokens

    @staticmethod
    def parse_extra_axioms(script):
        tokenizer = PTk.PropositionalProofTokenizer()
        tokens = tokenizer.tokenize(script)
        extras = {}
        while len(tokens) > 0:
            lhs, tokens = PExp.PropositionalExpression.parse_expression(tokens)
            rhs, name, tokens = PropositionalProof.parse_eq_rhs_reason(tokens)
            extras[name] = (lhs, rhs)
        return extras

    @staticmethod
    def parse_proof_script(script):
        tokenizer = PTk.PropositionalProofTokenizer()
        tokens = tokenizer.tokenize(script)
        expr, tokens = PExp.PropositionalExpression.parse_expression(tokens)
        steps = [(expr, None)]
        while len(tokens) > 0:
            expr, name, tokens = PropositionalProof.parse_eq_rhs_reason(tokens)
            steps.append((expr, name))
        return steps

    def check_proof(self, script=None):
        if script is not None:
            if isinstance(script, str):
                self.steps = PropositionalProof.parse_proof_script(script)
            else:
                self.steps = script
        print(self.steps)
        errors = []
        if len(self.steps) == 0:
            errors.append("Proof is empty")
            return errors
        if self.steps[0][0].equal(self.lhs):
            left_to_right = True
        elif self.steps[0][0].equal(self.rhs):
            left_to_right = False
        else:
            errors.append("First step does not match either the left- or right-hand side "
                          + "of the theorem you want to prove")
            left_to_right = None
        for i in range(1, len(self.steps)):
            if self.steps[i][1] in self.axioms:
                axiom = self.axioms[self.steps[i][1]]
            else:
                errors.append("Step {} uses an unknown axiom: {}".format(i + 1, self.steps[i][1]))
                continue
            _, error_msg = self.does_axiom_apply(axiom, self.steps[i-1][0], self.steps[i][0])
            if error_msg is None:
                errors.append("Step {} does nothing".format(i + 1))
                continue
            elif error_msg is not True:
                errors.append("Step {} {}".format(i + 1, error_msg))
        if left_to_right is None:
            if not (self.steps[-1][0].equal(self.lhs) or self.steps[0][0].equal(self.rhs)):
                errors.append("Last step does not match either the left- or right-hand side "
                              + "of the theorem you want to prove")
        elif left_to_right:
            if not self.steps[-1][0].equal(self.rhs):
                errors.append("Last step does not match the right-hand side of the theorem you want to prove")
        else:
            if not self.steps[-1][0].equal(self.lhs):
                errors.append("Last step does not match the left-hand side of the theorem you want to prove")
        return errors

    def does_axiom_apply(self, axiom, lhs, rhs):
        if lhs.equal(rhs):
            return None, None
        m = self.valid_axiom_application(axiom, lhs, rhs)
        if m is True:
            return True, True
        partial_match = m is None
        if type(lhs) == type(rhs):
            found_diff = False
            for lhs_i, rhs_i in zip(lhs.children(), rhs.children()):
                p_i, m_i = self.does_axiom_apply(axiom, lhs_i, rhs_i)
                if p_i:
                    partial_match = True
                if m_i is None:
                    continue
                if m_i is True:
                    if found_diff:
                        return partial_match, "takes more than one step at a time"
                    found_diff = True
                else:
                    return partial_match, m_i
            return partial_match, True
        if partial_match:
            return True, "result does not follow from applying axiom correctly"
        else:
            return False, "does not match axiom used"

    @staticmethod
    def valid_axiom_application(axiom, lhs, rhs):
        matcher = PMatch.PropositionalMatcher()
        matcher.reset()
        partial_match = False
        if matcher.match(axiom[0], lhs):
            if matcher.replace(axiom[1]).equal(rhs):
                return True
            partial_match = True
        if matcher.match(axiom[0], rhs):
            if matcher.replace(axiom[1]).equal(lhs):
                return True
            partial_match = True
        if partial_match:
            return False
        return None

# # proof_script = """
# # (x \\/ y) /\\ y
# # = (x \\/ y) /\\ (y \\/ False) { \\/ identity }
# # = (y \\/ x) /\\ (y \\/ False) { \\/ commutative }
# # = y \\/ (x /\\ False) { \\/ distributive }
# # = y \\/ False { /\\ null }
# # = y  { \\/ identity }
# # """
#
# proof = PropositionalProof("(x \\/ y) /\\ y",
#                            "y",
#                            "x /\\ False = False { /\\ null }")

# proof_script = """
# ~false
# = ~(false \\/ false) {\\/ identity}
# = ~(~(~false)) \\/ false) {double negation}
# = ~((~false) ==> false) {implication}
# = ~(~true) {self-implication}
# = true {double negation}
# """
#
# proof = PropositionalProof("~false",
#                            "true",
#                            "x /\\ False = False { /\\ null }")
# errors0 = proof.check_proof(proof_script)
# print(errors0)

# response = {"lhs": "(x \\\\/ y) /\\\\ y", "rhs": "y", "extra_axioms": "", "proof": "                (x \\\\/ y) /\\\\ y \r\n              = (x \\\\/ y) /\\\\ (y \\\\/ False)     { \\\\/ identity } \r\n              = (y \\\\/ x) /\\\\ (y \\\\/ False)     { \\\\/ commutative } \r\n              = y \\\\/ (x /\\\\ False)             { \\\\/ distributive } \r\n              = y \\\\/ False                     { /\\\\ null } \r\n              = y                               { \\\\/ identity }\r\n            ", "errors": []}
#
# proof = PropositionalProof(response["lhs"],
#                            response["rhs"],
#                            response["extra_axioms"])
# errors0 = proof.check_proof(response["proof"])
# print(errors0)
