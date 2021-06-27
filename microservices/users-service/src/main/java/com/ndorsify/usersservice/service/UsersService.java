package com.ndorsify.usersservice.service;

import com.ndorsify.usersservice.dto.request.UsersRequestDto;
import com.ndorsify.usersservice.dto.response.UsersResponseDto;
import com.ndorsify.usersservice.entity.Users;
import com.ndorsify.usersservice.repository.UsersRepository;
import com.ndorsify.usersservice.util.UtilService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.convert.converter.Converter;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class UsersService {

    @Autowired
    private UsersRepository usersRepository;

    public Page<UsersResponseDto> getAllUsersPage(Pageable page) {
        return usersRepository.findAll(page)
                .map(new Function<Users, UsersResponseDto>() {
                    @Override
                    public UsersResponseDto apply(Users users) {
                        return UtilService.usersEntityToUsersResponseDto(users);
                    }
                });
    }
    public List<UsersResponseDto> getAllUsers(Pageable page) {
        return usersRepository.findAll(page)
                .getContent()
                .stream()
                .map(UtilService::usersEntityToUsersResponseDto)
                .collect(Collectors.toList());
    }

    public Users getUsersById(Long id) {
        return usersRepository.findById(id).get();
    }

    public UsersResponseDto createUsers(UsersRequestDto usersRequestDto) {
        Users users = UtilService.userRequestDtoToUsersEntity(usersRequestDto);
        return UtilService.usersEntityToUsersResponseDto(usersRepository.save(users));
    }

    public ResponseEntity<UsersResponseDto> updateUsers(Long id, UsersRequestDto usersRequestDto) {
        Users users = UtilService.userRequestDtoToUsersEntity(usersRequestDto);
        Optional<Users> users1 = this.usersRepository.findById(id);

        if(users1.isPresent()){
            users.setId(users1.get().getId());
            return ResponseEntity.ok().body(UtilService.usersEntityToUsersResponseDto(this.usersRepository.save(users)));
        }
        else {
            return ResponseEntity.notFound().build();
        }
    }
}
