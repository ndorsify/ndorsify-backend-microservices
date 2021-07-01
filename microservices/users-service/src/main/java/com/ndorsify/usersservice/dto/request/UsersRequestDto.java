package com.ndorsify.usersservice.dto.request;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class UsersRequestDto {

    private String firstName;

    private String lastName;

    private String email;

    private String imageUrl;

    private String country;

}
