package com.example.simpleapp.dto;

import jakarta.validation.constraints.Size;

public record UpdateUserRequest(
    @Size(max = 100, message = "Name must not exceed 100 characters")
    String name
) {}
