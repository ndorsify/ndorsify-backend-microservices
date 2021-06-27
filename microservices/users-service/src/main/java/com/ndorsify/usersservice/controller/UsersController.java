package com.ndorsify.usersservice.controller;

import com.ndorsify.usersservice.dto.request.UsersRequestDto;
import com.ndorsify.usersservice.dto.response.UsersResponseDto;
import com.ndorsify.usersservice.service.UsersService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/users")
public class UsersController {

    @Autowired
    private UsersService usersService;

    @GetMapping("list")
    public List<UsersResponseDto> getAllList(@RequestParam(defaultValue = "0") int page,
                                             @RequestParam(defaultValue = "10") int size,
                                             @RequestParam(name = "sortBy", defaultValue = "id") String sortBy){
        Pageable firstPageWithTwoElements = PageRequest.of(page, size, Sort.by(sortBy));
        return usersService.getAllUsers(firstPageWithTwoElements);
    }
    @GetMapping
    public Page<UsersResponseDto> getAllPage(@RequestParam(defaultValue = "0") int page,
                                             @RequestParam(defaultValue = "10") int size,
                                             @RequestParam(name = "sortBy", defaultValue = "id") String sortBy){
        Pageable firstPageWithTwoElements = PageRequest.of(page, size, Sort.by(sortBy));
        return usersService.getAllUsersPage(firstPageWithTwoElements);
    }
    @PostMapping
    public UsersResponseDto createUser(@RequestBody UsersRequestDto usersRequestDto){
        return usersService.createUsers(usersRequestDto);
    }

    @PutMapping("{id}")
    public ResponseEntity<UsersResponseDto> updateUser(@PathVariable Long id,
                                                       @RequestBody UsersRequestDto usersRequestDto){
        return usersService.updateUsers(id, usersRequestDto);
    }
}
