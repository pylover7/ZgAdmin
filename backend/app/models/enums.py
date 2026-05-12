from enum import Enum


class EnumBase(Enum):
    @classmethod
    def get_member_values(cls):
        return [item.value for item in cls.__members__.values()]

    @classmethod
    def get_member_names(cls):
        return list(cls.__members__.keys())


class IntEnum(int, EnumBase):
    ...


class StrEnum(str, EnumBase):
    ...


class MethodType(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
