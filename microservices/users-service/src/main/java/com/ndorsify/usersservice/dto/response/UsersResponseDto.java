package com.ndorsify.usersservice.dto.response;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class UsersResponseDto {

    private Long id;

    private String firstName;

    private String lastName;

    private String email;

    private String imageUrl;
}
