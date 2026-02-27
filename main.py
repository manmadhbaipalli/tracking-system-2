from calculator import Calculator


def main():
    print("=== Simple Python Calculator ===")
    print("Operations: +, -, *, /")
    print("Type 'exit' to quit")
    print()

    calc = Calculator()

    while True:
        user_input = input("Enter expression (e.g., 5 + 3): ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        parts = user_input.split()
        if len(parts) != 3:
            print("Invalid format. Use: <number> <operator> <number>")
            continue

        try:
            a = float(parts[0])
            op = parts[1]
            b = float(parts[2])
            result = calc.calculate(a, op, b)
            print(f"Result: {result:.4f}\n")
        except ValueError as e:
            print(f"Error: {e}")
        except ZeroDivisionError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
