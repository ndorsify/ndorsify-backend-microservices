package com.ndorsify.dynamiccontentservice.util;

import com.ndorsify.dynamiccontentservice.dto.response.Questions;
import com.ndorsify.dynamiccontentservice.entity.Content;

public class UtilOnBoardCreator {

    public static Questions questionsFromContentEntity(Content content){
        Questions questions = new Questions();
        questions.setQuestion(content.getLookupValue1());
        questions.setDataType(content.getLookupText2());
        questions.setOptions(content.getLookupValue2());
        return  questions;
    }
}
