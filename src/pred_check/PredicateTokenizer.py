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
                Token('COMMA', ','),
                Token('LPAREN', '('),
                Token('RPAREN', ')'),
                Token('LBRACKET', '['),
                Token('RBRACKET', ']')
                ]

_EXTRA_TOKENS = [Token('LBRACE', '{'),
                 Token('RBRACE', '}'),
                 Token('EQ', '='),
                 Token('HYPHEN', '-'),
                 Token('IMPLIEDBY', '-|')
                 ]


class PredicateTokenizer:
    def __init__(self, tokens=None):
        if tokens is None:
            tokens = _BASE_TOKENS
        self.tokens = sorted(tokens, key=lambda token: len(token.value), reverse=True)

    def tokenize(self, expr):
        var_re = re.compile("[a-zA-Z_][a-zA-Z0-9_]*")
        const_re = re.compile("[0-9]+")
        tokens = []
        s = expr.replace("\\\\", "\\").lower()
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
                    word = s[m.start():m.end()]
                    if word == "true":
                        tokens.append(Token('PROP', True))
                    elif word == "false":
                        tokens.append(Token('PROP', False))
                    elif word in ["forall", "all"]:
                        tokens.append(Token('ALL', word))
                    elif word in ["exists", "some"]:
                        tokens.append(Token('EXISTS', word))
                    else:
                        tokens.append(Token('VAR', word))
                    s = s[m.end():]
                else:
                    m = const_re.match(s)
                    if m:
                        word = int(s[m.start():m.end()])
                        tokens.append(Token('CONST', word))
                        s = s[m.end():]
                    else:
                        raise ValueError("Unexpected token starting at: " + s)
        return tokens

    @staticmethod
    def stringify_tokens(tokens):
        return " ".join([token.to_string() for token in tokens[:20]])


class PredicateProofTokenizer(PredicateTokenizer):
    def __init__(self):
        super().__init__(_BASE_TOKENS + _EXTRA_TOKENS)
