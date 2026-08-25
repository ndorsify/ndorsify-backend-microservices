"""Entity -> DTO mapping — port of the Java ``UtilOnBoardCreator``."""
from ..models.content import Content
from ..schemas.questions import Questions


def questions_from_content_entity(content: Content) -> Questions:
    return Questions(
        question=content.lookup_value1,
        dataType=content.lookup_text2,
        options=content.lookup_value2,
    )
