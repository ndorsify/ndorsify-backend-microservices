package com.ndorsify.dynamiccontentservice.entity;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Data
@AllArgsConstructor
@NoArgsConstructor
public class Content {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String lookupText1; //Hold the type

    private String lookupValue1;// Hold the question

    private String lookupText2;// Holds the dataType

    private String lookupValue2;// Holds the options

    private String lookupText3;// Holds the category

    private String createdBy;

    private String modifiedBy;

    @CreationTimestamp
    private LocalDateTime createdDate;
    @UpdateTimestamp
    private LocalDateTime modifiedDate;

    private boolean isActive;

    private boolean isDeleted;
}
