"""Entity <-> DTO mapping — port of the Java ``UtilService`` static methods."""
from ..models.users import Users
from ..schemas.users import UsersRequestDto, UsersResponseDto

# camelCase API sort keys -> ORM column names. Mirrors Sort.by(sortBy) in Java,
# which accepted entity property names. Unknown keys fall back to "id".
SORT_FIELD_MAP = {
    "id": "id",
    "firstName": "first_name",
    "lastName": "last_name",
    "email": "email",
    "imageUrl": "image_url",
    "role": "role",
    "createdDate": "created_date",
    "modifiedDate": "modified_date",
}


def resolve_sort_column(sort_by: str) -> str:
    return SORT_FIELD_MAP.get(sort_by, "id")


def user_request_dto_to_entity(dto: UsersRequestDto) -> Users:
    return Users(
        first_name=dto.firstName,
        last_name=dto.lastName,
        email=dto.email,
        image_url=dto.imageUrl,
    )


def user_entity_to_response_dto(user: Users) -> UsersResponseDto:
    return UsersResponseDto(
        id=user.id,
        firstName=user.first_name,
        lastName=user.last_name,
        email=user.email,
        imageUrl=user.image_url,
    )
