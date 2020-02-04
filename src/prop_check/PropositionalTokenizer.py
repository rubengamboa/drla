import re


class Token:
    def __init__(self, tok_type, value):
        self.type = tok_type
        self.value = value

    def __str__(self):
        return "<" + self.type + ": " + str(self.value) + ">"

    def __repr__(self):
        return str(self)

    def to_string(self):
        return str(self.value)

_BASE_TOKENS = [Token('OR', '\\/'),
                Token('AND', '/\\'),
                Token('NOT', '~'),
                Token('IMPLIES', '==>'),
                Token('IFF', '<=>'),
                Token('LPAREN', '('),
                Token('RPAREN', ')')]

_EXTRA_TOKENS = [Token('LBRACE', '{'),
                 Token('RBRACE', '}'),
                 Token('EQ', '='),
                 Token('HYPHEN', '-'),
                 ]


class PropositionalTokenizer:
    def __init__(self, tokens=None):
        if tokens is None:
            tokens = _BASE_TOKENS
        self.tokens = sorted(tokens, key=lambda token: len(token.value), reverse=True)

    def tokenize(self, expr):
        var_re = re.compile("[a-zA-Z_][a-zA-Z0-9_]*")
        tokens = []
        s = expr.replace("\\\\","\\").lower()
        while True:
            s = s.lstrip()
            if s == "":
                break
            for token in self.tokens:
                if s.startswith(token.value):
                    tokens.append(token)
                    s = s[len(token.value):]
                    break
            else:
                m = var_re.match(s)
                if m:
                    if s[m.start():m.end()] == "true":
                        tokens.append(Token('PROP', True))
                    elif s[m.start():m.end()] == "false":
                        tokens.append(Token('PROP', False))
                    else:
                        tokens.append(Token('VAR', s[m.start():m.end()]))
                    s = s[m.end():]
                else:
                    raise ValueError("Unexpected token starting at: " + s)
        return tokens

    @staticmethod
    def stringify_tokens(tokens):
        return " ".join([token.to_string() for token in tokens])


class PropositionalProofTokenizer(PropositionalTokenizer):
    def __init__(self):
        super().__init__(_BASE_TOKENS + _EXTRA_TOKENS)
