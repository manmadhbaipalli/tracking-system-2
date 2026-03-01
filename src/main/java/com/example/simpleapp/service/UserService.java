package com.example.simpleapp.service;

import com.example.simpleapp.dto.UpdateUserRequest;
import com.example.simpleapp.dto.UserResponse;
import com.example.simpleapp.exception.ForbiddenException;
import com.example.simpleapp.exception.NotFoundException;
import com.example.simpleapp.model.User;
import com.example.simpleapp.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class UserService {

    private static final Logger log = LoggerFactory.getLogger(UserService.class);

    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public UserResponse findById(Long id, String currentUserEmail) {
        log.info("Finding user with id: {} for user: {}", id, currentUserEmail);
        User user = userRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("User not found with id: " + id));

        if (!user.getEmail().equals(currentUserEmail)) {
            throw new ForbiddenException("You can only access your own user data");
        }

        return toResponse(user);
    }

    @Transactional
    public UserResponse update(Long id, UpdateUserRequest request, String currentUserEmail) {
        log.info("Updating user with id: {} for user: {}", id, currentUserEmail);
        User user = userRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("User not found with id: " + id));

        if (!user.getEmail().equals(currentUserEmail)) {
            throw new ForbiddenException("You can only update your own user data");
        }

        if (request.name() != null && !request.name().isBlank()) {
            user.setName(request.name());
        }

        User updatedUser = userRepository.save(user);
        log.info("User updated successfully: {}", updatedUser.getId());
        return toResponse(updatedUser);
    }

    @Transactional
    public void deactivate(Long id, String currentUserEmail) {
        log.info("Deactivating user with id: {} for user: {}", id, currentUserEmail);
        User user = userRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("User not found with id: " + id));

        if (!user.getEmail().equals(currentUserEmail)) {
            throw new ForbiddenException("You can only deactivate your own user account");
        }

        user.setActive(false);
        userRepository.save(user);
        log.info("User deactivated successfully: {}", user.getId());
    }

    private UserResponse toResponse(User user) {
        return new UserResponse(
                user.getId(),
                user.getEmail(),
                user.getName(),
                user.getRole().name(),
                user.isActive(),
                user.getCreatedAt()
        );
    }
}
