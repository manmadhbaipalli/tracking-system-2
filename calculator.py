class Calculator:
    """Handles basic arithmetic operations."""

    def calculate(self, a: float, operator: str, b: float) -> float:
        ops = {
            "+": self.add,
            "-": self.subtract,
            "*": self.multiply,
            "/": self.divide,
        }
        if operator not in ops:
            raise ValueError(f"Unknown operator: {operator}")
        return ops[operator](a, b)

    def add(self, a: float, b: float) -> float:
        return a + b

    def subtract(self, a: float, b: float) -> float:
        return a - b

    def multiply(self, a: float, b: float) -> float:
        return a * b

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ZeroDivisionError("Division by zero is not allowed")
        return a / b
