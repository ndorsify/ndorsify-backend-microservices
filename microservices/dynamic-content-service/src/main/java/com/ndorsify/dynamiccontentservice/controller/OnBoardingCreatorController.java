package com.ndorsify.dynamiccontentservice.controller;

import com.ndorsify.dynamiccontentservice.dto.response.Questions;
import com.ndorsify.dynamiccontentservice.service.OnBoardingCreatorService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/onboard/creator")
public class OnBoardingCreatorController {

    @Autowired
    private OnBoardingCreatorService onBoardingCreatorService;

    @GetMapping("questions")
    public List<Questions> getQuestions(){
        return onBoardingCreatorService.allQuestion();
    }
}
