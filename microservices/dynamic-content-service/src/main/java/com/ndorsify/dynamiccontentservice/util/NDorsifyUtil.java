package com.ndorsify.dynamiccontentservice.util;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class NDorsifyUtil<T> {

    private String status;

    private String message;

    private T data;
}
