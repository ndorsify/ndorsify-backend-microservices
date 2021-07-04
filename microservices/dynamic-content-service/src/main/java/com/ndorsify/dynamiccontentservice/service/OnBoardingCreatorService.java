package com.ndorsify.dynamiccontentservice.service;

import com.ndorsify.dynamiccontentservice.dto.response.Questions;
import com.ndorsify.dynamiccontentservice.entity.Content;
import com.ndorsify.dynamiccontentservice.repository.ContentRepository;
import com.ndorsify.dynamiccontentservice.util.UtilOnBoardCreator;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class OnBoardingCreatorService {

    @Autowired
    private ContentRepository contentRepository;

    public Map<String, List<Questions>> allQuestion(){
        Set<String> categorySet = new LinkedHashSet<>();
        Map<String, List<Questions>> listMap = new LinkedHashMap<>();
        String text1 = "creator-onboard-questions";
        List<Content> contentList = contentRepository.findAllByLookupText1(text1);
        contentList.forEach(content -> categorySet.add(content.getLookupText3()));
        categorySet.forEach(cat -> {
            List<Questions> questionsList = contentList
                    .stream()
                    .filter(content -> content.getLookupText3().equals(cat))
                    .map(UtilOnBoardCreator::questionsFromContentEntity)
                    .collect(Collectors.toList());
            listMap.put(cat, questionsList);
        });
       return listMap;
    }
}
