package com.example;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;

class CalculatorTest {

    private Calculator calculator;

    @BeforeEach
    void setUp() {
        calculator = new Calculator();
    }

    @Test
    void testAdd() {
        assertEquals(8.0, calculator.add(5, 3));
        assertEquals(0.0, calculator.add(-3, 3));
        assertEquals(-6.0, calculator.add(-3, -3));
    }

    @Test
    void testSubtract() {
        assertEquals(2.0, calculator.subtract(5, 3));
        assertEquals(-6.0, calculator.subtract(-3, 3));
    }

    @Test
    void testMultiply() {
        assertEquals(15.0, calculator.multiply(5, 3));
        assertEquals(0.0, calculator.multiply(5, 0));
        assertEquals(-15.0, calculator.multiply(-5, 3));
    }

    @Test
    void testDivide() {
        assertEquals(2.5, calculator.divide(5, 2));
        assertEquals(-2.5, calculator.divide(-5, 2));
    }

    @Test
    void testDivideByZero() {
        assertThrows(ArithmeticException.class, () -> calculator.divide(5, 0));
    }

    @Test
    void testCalculateWithOperator() {
        assertEquals(8.0, calculator.calculate(5, "+", 3));
        assertEquals(2.0, calculator.calculate(5, "-", 3));
        assertEquals(15.0, calculator.calculate(5, "*", 3));
        assertEquals(2.5, calculator.calculate(5, "/", 2));
    }

    @Test
    void testUnknownOperator() {
        assertThrows(IllegalArgumentException.class, () -> calculator.calculate(5, "%", 3));
    }
}
