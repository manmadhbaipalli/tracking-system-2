package com.example.simpleapp.dto;

public record AuthResponse(
    String token,
    String type,
    Long userId,
    String email,
    String name,
    String role
) {
    public AuthResponse(String token, Long userId, String email, String name, String role) {
        this(token, "Bearer", userId, email, name, role);
    }
}
