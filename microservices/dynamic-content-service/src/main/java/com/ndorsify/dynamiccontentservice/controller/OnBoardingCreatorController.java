package com.ndorsify.dynamiccontentservice.controller;

import com.ndorsify.dynamiccontentservice.dto.response.Questions;
import com.ndorsify.dynamiccontentservice.service.OnBoardingCreatorService;
import com.ndorsify.dynamiccontentservice.util.NDorsifyUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/onboard/creator")
public class OnBoardingCreatorController {

    @Autowired
    private OnBoardingCreatorService onBoardingCreatorService;

    @GetMapping("questions")
    public NDorsifyUtil<Map<String, List<Questions>>> getQuestions(){
        NDorsifyUtil<Map<String, List<Questions>>> nDorsifyUtil = new NDorsifyUtil<>();
        nDorsifyUtil.setStatus("success");
        nDorsifyUtil.setMessage("success");
        Map<String, List<Questions>> listMap = onBoardingCreatorService.allQuestion();
        nDorsifyUtil.setData(listMap);
        return nDorsifyUtil;
    }
}
