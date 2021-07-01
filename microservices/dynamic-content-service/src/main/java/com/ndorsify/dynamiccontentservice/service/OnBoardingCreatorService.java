package com.ndorsify.dynamiccontentservice.service;

import com.ndorsify.dynamiccontentservice.dto.response.Questions;
import com.ndorsify.dynamiccontentservice.repository.ContentRepository;
import com.ndorsify.dynamiccontentservice.util.UtilOnBoardCreator;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class OnBoardingCreatorService {

    @Autowired
    private ContentRepository contentRepository;

    public List<Questions> allQuestion(){
        String text1 = "creator-onboard-questions";
        return contentRepository.findAllByLookupText1(text1)
                .stream()
                .map(UtilOnBoardCreator::questionsFromContentEntity)
                .collect(Collectors.toList());
    }
}
