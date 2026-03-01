package com.example.simpleapp.dto;

import java.time.Instant;

public record UserResponse(
    Long id,
    String email,
    String name,
    String role,
    boolean active,
    Instant createdAt
) {}
