package com.example;

import java.util.Scanner;

/**
 * Simple Java Application - Interactive Calculator
 */
public class Main {

    public static void main(String[] args) {
        System.out.println("=== Simple Java Calculator ===");
        System.out.println("Operations: +, -, *, /");
        System.out.println("Type 'exit' to quit");
        System.out.println();

        Calculator calculator = new Calculator();
        Scanner scanner = new Scanner(System.in);

        while (true) {
            System.out.print("Enter expression (e.g., 5 + 3): ");
            String input = scanner.nextLine().trim();

            if (input.equalsIgnoreCase("exit")) {
                System.out.println("Goodbye!");
                break;
            }

            try {
                String[] parts = input.split("\\s+");
                if (parts.length != 3) {
                    System.out.println("Invalid format. Use: <number> <operator> <number>");
                    continue;
                }

                double a = Double.parseDouble(parts[0]);
                String op = parts[1];
                double b = Double.parseDouble(parts[2]);

                double result = calculator.calculate(a, op, b);
                System.out.printf("Result: %.4f%n%n", result);

            } catch (NumberFormatException e) {
                System.out.println("Error: Invalid number format.");
            } catch (ArithmeticException e) {
                System.out.println("Error: " + e.getMessage());
            } catch (IllegalArgumentException e) {
                System.out.println("Error: " + e.getMessage());
            }
        }

        scanner.close();
    }
}
