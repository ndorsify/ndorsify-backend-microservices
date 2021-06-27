package com.ndorsify.usersservice.util;

import com.ndorsify.usersservice.dto.request.UsersRequestDto;
import com.ndorsify.usersservice.dto.response.UsersResponseDto;
import com.ndorsify.usersservice.entity.Users;
import org.springframework.beans.BeanUtils;

public class UtilService {

    public static Users userRequestDtoToUsersEntity(UsersRequestDto usersRequestDto){
        Users users = new Users();
        BeanUtils.copyProperties(usersRequestDto, users);
        return users;
    }

    public static UsersResponseDto usersEntityToUsersResponseDto(Users users){
        UsersResponseDto usersResponseDto = new UsersResponseDto();
        BeanUtils.copyProperties(users, usersResponseDto);
        return usersResponseDto;
    }
}
