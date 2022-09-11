from app.models.config_model import ConfigModel


class CustomBaseException(ConfigModel):
    error_codes: list = []
    description: str | None = None
    phrase: str | None = None
    message: str | None = None
    fields: list = []
