import ast
import operator

# Supported operators mapping
BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Div: lambda a, b: a // b,  # Prompt specifies / is integer floor division
    ast.Pow: operator.pow,
}

COMP_OPS = {
    ast.Eq: operator.eq,
    ast.Lt: operator.lt,
    ast.Gt: operator.gt,
}

BOOL_OPS = {
    ast.And: lambda a, b: bool(a) and bool(b),
    ast.Or: lambda a, b: bool(a) or bool(b),
}

class ExpressionEvaluator(ast.NodeVisitor):
    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Constant(self, node):
        if isinstance(node.value, (int, bool)):
            return node.value
        raise TypeError(f"Unsupported constant type: {type(node.value)}")

    def visit_Num(self, node):  # For older Python AST compatibility
        return node.n

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_type = type(node.op)
        if op_type in BIN_OPS:
            # Handle Python / operator returning float in newer AST if parsed as Div
            if op_type is ast.Div:
                return left // right
            return BIN_OPS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type}")

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        elif isinstance(node.op, ast.UAdd):
            return +operand
        elif isinstance(node.op, ast.Not):
            return not operand
        raise ValueError(f"Unsupported unary operator: {type(node.op)}")

    def visit_Compare(self, node):
        left = self.visit(node.left)
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise ValueError("Chained comparisons not supported")
        op_type = type(node.ops[0])
        right = self.visit(node.comparators[0])
        if op_type in COMP_OPS:
            return COMP_OPS[op_type](left, right)
        raise ValueError(f"Unsupported comparison operator: {op_type}")

    def visit_BoolOp(self, node):
        op_type = type(node.op)
        if op_type in BOOL_OPS:
            val = self.visit(node.values[0])
            for next_node in node.values[1:]:
                if op_type is ast.And and not val:
                    return False
                if op_type is ast.Or and val:
                    return True
                val = BOOL_OPS[op_type](val, self.visit(next_node))
            return val
        raise ValueError(f"Unsupported boolean operator: {op_type}")

    def generic_visit(self, node):
        raise ValueError(f"Unsupported expression construct: {type(node)}")

def eval_expr(expr: str) -> int | bool:
    # Preprocess '^' to '**' for Python expression parser
    # Be careful with spacing or replace '^'
    # Simple token-based or character replacement where ^ is exponentiation
    # Since identifiers/numbers don't contain ^ except as operator:
    processed_expr = expr.replace('^', '**')
    try:
        tree = ast.parse(processed_expr, mode='eval')
    except SyntaxError as e:
        raise ValueError(f"Invalid expression syntax: {expr}") from e
    
    evaluator = ExpressionEvaluator()
    result = evaluator.visit(tree)
    if not isinstance(result, (int, bool)):
        raise TypeError(f"Expression evaluated to unsupported type: {type(result)}")
    return result
