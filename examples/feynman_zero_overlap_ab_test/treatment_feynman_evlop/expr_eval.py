import re

class ExprError(Exception):
    pass

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.len = len(text)

    def tokenize(self):
        tokens = []
        i = 0
        while i < self.len:
            c = self.text[i]
            if c.isspace():
                i += 1
                continue
            if c in "+-*/^()<>=":
                if c == '<' and i + 1 < self.len and self.text[i+1] == '=':
                    tokens.append(('OP', '<='))
                    i += 2
                    continue
                if c == '>' and i + 1 < self.len and self.text[i+1] == '=':
                    tokens.append(('OP', '>='))
                    i += 2
                    continue
                if c == '=' and i + 1 < self.len and self.text[i+1] == '=':
                    tokens.append(('OP', '=='))
                    i += 2
                    continue
                tokens.append(('OP', c))
                i += 1
                continue
            if c.isdigit():
                start = i
                while i < self.len and self.text[i].isdigit():
                    i += 1
                tokens.append(('INT', int(self.text[start:i])))
                continue
            if c.isalpha() or c == '_':
                start = i
                while i < self.len and (self.text[i].isalnum() or self.text[i] == '_'):
                    i += 1
                word = self.text[start:i]
                if word in ('and', 'or', 'True', 'False'):
                    tokens.append((word.upper(), word))
                else:
                    raise ExprError(f"Unknown identifier/keyword: {word}")
                continue
            raise ExprError(f"Unexpected character: {c}")
        tokens.append(('EOF', None))
        return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def consume(self, expected_type=None, expected_val=None):
        t_type, t_val = self.peek()
        if expected_type and t_type != expected_type:
            raise ExprError(f"Expected token type {expected_type}, got {t_type}")
        if expected_val and t_val != expected_val:
            raise ExprError(f"Expected token value {expected_val}, got {t_val}")
        self.pos += 1
        return t_val

    def parse(self):
        node = self.parse_or()
        if self.peek()[0] != 'EOF':
            raise ExprError(f"Unexpected trailing token: {self.peek()}")
        return node

    def parse_or(self):
        node = self.parse_and()
        while self.peek()[1] == 'or':
            self.consume('OR', 'or')
            right = self.parse_and()
            node = ('OR', node, right)
        return node

    def parse_and(self):
        node = self.parse_comparison()
        while self.peek()[1] == 'and':
            self.consume('AND', 'and')
            right = self.parse_comparison()
            node = ('AND', node, right)
        return node

    def parse_comparison(self):
        node = self.parse_additive()
        while self.peek()[0] == 'OP' and self.peek()[1] in ('<', '>', '<=', '>=', '=='):
            op = self.consume()
            right = self.parse_additive()
            node = ('COMP', op, node, right)
        return node

    def parse_additive(self):
        node = self.parse_multiplicative()
        while self.peek()[0] == 'OP' and self.peek()[1] in ('+', '-'):
            op = self.consume()
            right = self.parse_multiplicative()
            node = ('BIN', op, node, right)
        return node

    def parse_multiplicative(self):
        node = self.parse_exponent()
        while self.peek()[0] == 'OP' and self.peek()[1] in ('*', '/'):
            op = self.consume()
            right = self.parse_exponent()
            node = ('BIN', op, node, right)
        return node

    def parse_exponent(self):
        # Unary binds tighter than exponentiation in mathematical convention for -2^2 = -(2^2) = -4,
        # or exponent applies to unary: parse unary first as base, or parse exponent where base can be unary.
        node = self.parse_unary()
        if self.peek()[0] == 'OP' and self.peek()[1] == '^':
            self.consume('OP', '^')
            right = self.parse_exponent()
            node = ('BIN', '^', node, right)
        return node

    def parse_unary(self):
        t_type, t_val = self.peek()
        if t_type == 'OP' and t_val in ('-', '+'):
            op = self.consume()
            operand = self.parse_exponent()  # Unary applies to exponent so -2^2 -> -(2^2)
            return ('UNARY', op, operand)
        return self.parse_primary()

    def parse_primary(self):
        t_type, t_val = self.peek()
        if t_type == 'INT':
            self.consume()
            return ('LIT', t_val)
        if t_type == 'TRUE':
            self.consume()
            return ('LIT', True)
        if t_type == 'FALSE':
            self.consume()
            return ('LIT', False)
        if t_type == 'OP' and t_val == '(':
            self.consume('OP', '(')
            node = self.parse_or()
            self.consume('OP', ')')
            return node
        raise ExprError(f"Unexpected token in primary: {t_type}, {t_val}")

def evaluate_ast(node):
    if not isinstance(node, tuple):
        return node
    ntype = node[0]
    if ntype == 'LIT':
        return node[1]
    elif ntype == 'UNARY':
        op, operand = node[1], evaluate_ast(node[2])
        if op == '-':
            return -operand
        elif op == '+':
            return +operand
    elif ntype == 'BIN':
        op, left_node, right_node = node[1], node[2], node[3]
        if op == '^':
            left = evaluate_ast(left_node)
            right = evaluate_ast(right_node)
            return left ** right
        
        left = evaluate_ast(left_node)
        right = evaluate_ast(right_node)
        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            if right == 0:
                raise ZeroDivisionError("division by zero")
            return left // right
    elif ntype == 'COMP':
        op, left_node, right_node = node[1], node[2], node[3]
        left = evaluate_ast(left_node)
        right = evaluate_ast(right_node)
        if op == '<':
            return left < right
        elif op == '>':
            return left > right
        elif op == '<=':
            return left <= right
        elif op == '>=':
            return left >= right
        elif op == '==':
            return left == right
    elif ntype == 'AND':
        left_node, right_node = node[1], node[2]
        left = evaluate_ast(left_node)
        if not left:
            return False
        right = evaluate_ast(right_node)
        return bool(right)
    elif ntype == 'OR':
        left_node, right_node = node[1], node[2]
        left = evaluate_ast(left_node)
        if left:
            return True
        right = evaluate_ast(right_node)
        return bool(right)
    raise ExprError(f"Unknown AST node type: {ntype}")

def eval_expr(expr: str) -> int | bool:
    lexer = Lexer(expr)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    return evaluate_ast(ast)
