from datetime import datetime, timezone

from pydantic import BaseConfig, BaseModel


def to_camel_case(string: str) -> str:
    return "".join(
        word if index == 0 else word.capitalize()
        for index, word in enumerate(string.split("_"))
    )


class ConfigModel(BaseModel):
    class Config(BaseConfig):
        allow_population_by_field_name = True
        use_enum_values = True
        anystr_strip_whitespace = True
        smart_union = True
        alias_generator = to_camel_case
        orm_mode = True
        json_encoders = {
            datetime: lambda dt: dt.replace(tzinfo=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
