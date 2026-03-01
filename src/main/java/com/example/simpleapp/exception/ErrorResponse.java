package com.example.simpleapp.exception;

import java.time.Instant;
import java.util.List;
import java.util.Map;

public record ErrorResponse(
        int status,
        String error,
        String message,
        Map<String, String> details,
        Instant timestamp
) {
    public static ErrorResponse of(int status, String error, String message) {
        return new ErrorResponse(status, error, message, null, Instant.now());
    }

    public static ErrorResponse withDetails(int status, String error, String message, List<FieldError> fieldErrors) {
        Map<String, String> details = fieldErrors != null
                ? fieldErrors.stream().collect(
                        java.util.stream.Collectors.toMap(FieldError::field, FieldError::message))
                : null;
        return new ErrorResponse(status, error, message, details, Instant.now());
    }

    public record FieldError(String field, String message) {}
}
