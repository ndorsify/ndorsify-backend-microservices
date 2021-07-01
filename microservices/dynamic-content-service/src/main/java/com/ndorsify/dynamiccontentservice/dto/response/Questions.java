package com.ndorsify.dynamiccontentservice.dto.response;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class Questions {

    private Long id;

    private String category;

    private String question;

    private String dataType;

    private String options;

}
