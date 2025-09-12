"""Calculator tool for mathematical operations."""

import ast
import operator
import math
from typing import List

from chat_agent.services.agent.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from chat_agent.utils.logger import get_logger

logger = get_logger("calculator_tool")


class CalculatorTool(BaseTool):
    """Tool for performing mathematical calculations."""
    
    # Safe operators for evaluation
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    # Safe functions
    SAFE_FUNCTIONS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'pi': math.pi,
        'e': math.e,
    }
    
    def get_name(self) -> str:
        return "calculator"
        
    def get_description(self) -> str:
        return "Perform mathematical calculations. Supports basic arithmetic, trigonometric functions, logarithms, and more."
        
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="expression",
                type=ToolParameterType.STRING,
                description="Mathematical expression to evaluate (e.g., '2 + 3 * 4', 'sqrt(16)', 'sin(pi/2)')",
                required=True
            )
        ]
        
    def _safe_eval(self, node):
        """Safely evaluate an AST node."""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.Name):
            if node.id in self.SAFE_FUNCTIONS:
                return self.SAFE_FUNCTIONS[node.id]
            else:
                raise ValueError(f"Unsafe name: {node.id}")
        elif isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            op = self.SAFE_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsafe operator: {type(node.op)}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            op = self.SAFE_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsafe unary operator: {type(node.op)}")
            return op(operand)
        elif isinstance(node, ast.Call):
            func = self._safe_eval(node.func)
            if not callable(func):
                raise ValueError(f"Not a function: {func}")
            args = [self._safe_eval(arg) for arg in node.args]
            return func(*args)
        elif isinstance(node, ast.List):
            return [self._safe_eval(item) for item in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self._safe_eval(item) for item in node.elts)
        else:
            raise ValueError(f"Unsafe node type: {type(node)}")
            
    async def execute(self, expression: str) -> ToolResult:
        """Execute the calculator tool."""
        try:
            logger.info(f"Calculating expression: {expression}")
            
            # Parse the expression
            try:
                tree = ast.parse(expression, mode='eval')
            except SyntaxError as e:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mathematical expression: {str(e)}"
                )
            
            # Evaluate safely
            try:
                result = self._safe_eval(tree.body)
                
                # Format result
                if isinstance(result, float):
                    # Round to reasonable precision
                    if result.is_integer():
                        result = int(result)
                    else:
                        result = round(result, 10)
                        
                logger.info(f"Calculation result: {result}")
                
                return ToolResult(
                    success=True,
                    result=result,
                    metadata={
                        "expression": expression,
                        "result_type": type(result).__name__
                    }
                )
                
            except (ValueError, TypeError, ZeroDivisionError, OverflowError) as e:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Calculation error: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Calculator tool error: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                result=None,
                error=f"Unexpected error: {str(e)}"
            )