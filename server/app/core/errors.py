from fastapi.exceptions import RequestValidationError
from fastapi.responses import UJSONResponse
from pydantic import EnumError, EnumMemberError, StrRegexError
from starlette.exceptions import HTTPException as StarletteHTTPException


def parse_error(err: any, field_names: list, raw: bool = True) -> dict | None:
    """
    Parse single error object (such as pydantic-based or fastapi-based) to dict

    :param err: Error object
    :param field_names: list of names of the field that are already processed
    :param raw: Whether this is a raw error or wrapped pydantic error
    :return: dict with name of the field (or "__all__") and actual message
    """
    if isinstance(err, list):
        permitted_values = ""
        for e in err:
            if isinstance(e.exc, EnumMemberError):
                permitted_values_temp = ", ".join(
                    [f"'{val}'" for val in e.exc.enum_values]
                )
                permitted_values += permitted_values_temp + " "
        message = (
            f"Value is not a valid enumeration member; "
            f"permitted: {permitted_values}."
        )
    elif isinstance(err.exc, EnumError):
        permitted_values = ", ".join([f"'{val}'" for val in err.exc.enum_values])
        message = (
            f"Value is not a valid enumeration member; "
            f"permitted: {permitted_values}."
        )
    elif isinstance(err.exc, StrRegexError):
        message = "Provided value doesn't match valid format"
    else:
        message = str(err.exc) or ""

    error_code = 400

    if isinstance(err, list):
        if hasattr(err[0].exc, "code") and err[0].exc.code.startswith("error_code"):
            error_code = int(err[0].exc.code.split(".")[-1])
    elif hasattr(err.exc, "code") and err.exc.code.startswith("error_code"):
        error_code = int(err.exc.code.split(".")[-1])

    if not raw:
        if len(err.loc_tuple()) == 2:
            if str(err.loc_tuple()[0]) in ["body", "query"]:
                name = err.loc_tuple()[1]
            else:
                name = err.loc_tuple()[0]
        elif len(err.loc_tuple()) == 1:
            if str(err.loc_tuple()[0]) == "body":
                name = "__all__"
            else:
                name = str(err.loc_tuple()[0])
        else:
            name = "__all__"
    else:
        if isinstance(err, list):
            if len(err[0].loc_tuple()) == 2:
                name = str(err[0].loc_tuple()[0])
            elif len(err[0].loc_tuple()) == 1:
                name = str(err[0].loc_tuple()[0])
            else:
                name = "__all__"
        else:
            if len(err.loc_tuple()) == 2:
                name = str(err.loc_tuple()[0])
            elif len(err.loc_tuple()) == 1:
                name = str(err.loc_tuple()[0])
            else:
                name = "__all__"

    if name in field_names:
        return None

    if message and not any(
        [message.endswith("."), message.endswith("?"), message.endswith("!")]
    ):
        message = message + "."
    return {"name": name, "message": message, "error_code": error_code}


def raw_errors_to_fields(raw_errors: list) -> list[dict]:
    """
    Translates list of raw errors (instances) into list of dicts with name/msg

    :param raw_errors: list with instances of raw error
    :return: list of dicts (1 dict for every raw error)
    """
    fields = []
    for top_err in raw_errors:
        if hasattr(top_err.exc, "raw_errors"):
            for err in top_err.exc.raw_errors:
                # This is a special case when errors happen both in request
                # handling & internal validation
                if isinstance(err, list):
                    err = err[0]
                field_err = parse_error(
                    err,
                    field_names=list(map(lambda x: x["name"], fields)),
                    raw=True,
                )
                if field_err is not None:
                    fields.append(field_err)
        else:
            field_err = parse_error(
                top_err,
                field_names=list(map(lambda x: x["name"], fields)),
                raw=False,
            )
            if field_err is not None:
                fields.append(field_err)
    return fields


async def http_exception_handler(_, exc: StarletteHTTPException) -> UJSONResponse:
    """
    Handles StarletteHTTPException, translating it into flat dict error data:
        * code - unique code of the error in the system
        * detail - general description of the error
        * fields - list of dicts with description of the error in each field

    :param _:
    :param exc: StarletteHTTPException instance
    :return: UJSONResponse with newly formatted error data
    """
    message = getattr(exc, "detail", "Validation error")
    if message and not any(
        [message.endswith("."), message.endswith("?"), message.endswith("!")]
    ):
        message = message + "."
    data = {
        "error_codes": [getattr(exc, "error_code", exc.status_code)],
        "description": getattr(exc, "description", None),
        "phrase": getattr(exc, "phrase", None),
        "message": message,
        "fields": getattr(exc, "fields", []),
    }
    return UJSONResponse(
        data, status_code=exc.status_code, headers=getattr(exc, "headers", None)
    )


async def validation_exception_handler(_, exc: RequestValidationError) -> UJSONResponse:
    """
    Handles ValidationError, translating it into flat dict error data:
        * code - unique code of the error in the system
        * detail - general description of the error
        * fields - list of dicts with description of the error in each field

    :param _:
    :param exc: StarletteHTTPException instance
    :return: UJSONResponse with newly formatted error data
    """
    status_code = getattr(exc, "status_code", 400)
    fields = raw_errors_to_fields(exc.raw_errors)

    if fields:
        error_codes = list(set(list(map(lambda x: x["error_code"], fields))))
    else:
        error_codes = [getattr(exc, "error_code", status_code)]

    message = getattr(exc, "message", "Validation error")
    if message and not any(
        [message.endswith("."), message.endswith("?"), message.endswith("!")]
    ):
        message = message + "."  # pragma: no cover

    data = {
        "error_codes": error_codes,
        "description": getattr(exc, "description", None),
        "phrase": getattr(exc, "phrase", None),
        "message": message,
        "fields": fields,
    }
    return UJSONResponse(
        data, status_code=status_code, headers=getattr(exc, "headers", None)
    )


async def not_found_error_handler(_, exc: RequestValidationError) -> UJSONResponse:
    return generic_error_handler(_, exc)


async def internal_server_error_handler(
    _, exc: RequestValidationError
) -> UJSONResponse:
    return generic_error_handler(_, exc)


def generic_error_handler(_, exc: Exception) -> UJSONResponse:
    data = {
        "error_codes": [getattr(exc, "error_code", 404)],
        "description": getattr(exc, "description", None),
        "phrase": getattr(exc, "phrase", None),
        "message": getattr(exc, "detail", "Not found"),
        "fields": getattr(exc, "fields", []),
    }
    return UJSONResponse(
        data,
        status_code=getattr(exc, "status_code", 404),
        headers=getattr(exc, "headers", None),
    )
