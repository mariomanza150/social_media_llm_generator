import re
from collections.abc import AsyncIterable, Iterable
from enum import Enum

from json_repair import repair_json
from openai import AsyncOpenAI
from outlines.models import openai
from outlines.models.openai import OpenAIConfig
from pydantic import BaseModel, model_validator
from starlette.background import BackgroundTask
from starlette.concurrency import iterate_in_threadpool
from starlette.responses import JSONResponse, StreamingResponse
from typing_extensions import Any, Union, get_args, get_origin


class Choices(str, Enum):
    @property
    def description(self) -> str:
        return self.value

    def as_jsonable(self):
        return {"value": self.name, "text": self.value}

    def __repr__(self):
        return f"{self.name} ({self.description})"


def is_enum(enum_type):
    expect_list = False
    if get_origin(enum_type) is Union:
        enum_type = get_args(enum_type)[0]
    if get_origin(enum_type) is list:
        enum_type = get_args(enum_type)[0]
        expect_list = True
    if issubclass(enum_type, Enum):
        return expect_list, enum_type
    return False, None


class Option(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def convert_to_enum(cls, values: Any) -> Any:
        enummed = {}
        print(cls)
        print(values)
        for field_name, field_info in cls.model_fields.items():
            expect_list, enum_type = is_enum(field_info.annotation)
            if enum_type is None:
                continue
            # print('enum recognized', enum_type)
            if isinstance(values, dict):
                value = values.pop(field_name, None)
            else:
                value = values
            if value is None:
                continue

            if isinstance(value, enum_type):
                enummed[field_name] = [value] if expect_list else value

            if isinstance(value, list) and expect_list:
                enummed[field_name] = []
                for val in value:
                    if isinstance(val, Enum):
                        enummed[field_name].append(val)
                    else:
                        try:
                            enummed[field_name].append(enum_type[val])
                        except KeyError:
                            try:
                                enummed[field_name].append(enum_type(val))
                            except ValueError as e:
                                print(e)

            if isinstance(value, str):
                try:
                    enummed[field_name] = enum_type[value]
                except KeyError:
                    try:
                        enummed[field_name] = enum_type(value)
                    except ValueError as e:
                        print(e)

        if isinstance(values, dict):
            return {**enummed, **values}
        return enummed

    @classmethod
    def get_options(cls, allowed_choices: dict[str, list[str]] = {}):
        options = {}
        for key, field_info in cls.model_fields.items():
            _, enum_type = is_enum(field_info.annotation)
            if enum_type is None:
                continue
            choices = []
            if key in allowed_choices:
                for choice in allowed_choices[key]:
                    choices.append(enum_type(choice))
            else:
                choices = list(enum_type)
            options[key] = choices
        return options

    @classmethod
    def get_json_options(cls, allowed_choices: dict[str, list[str]] = {}):
        options = cls.get_options(allowed_choices)
        json_options = {}
        for key, list in options.items():
            json_options[key] = [choice.as_jsonable() for choice in list]
        return json_options

    def get_enum_names(self):
        json_options = {}
        for key, field in self.model_fields.items():
            expect_list, enum_type = is_enum(field.annotation)
            if enum_type is None:
                continue
            value = getattr(self, key)
            if value is None:
                continue
            if isinstance(value, list) and expect_list:
                json_options[key] = [val.name for val in value if val is not None]
                continue
            json_options[key] = value.name
        return json_options

    def get_enums(self):
        json_options = {}
        for key, field in self.model_fields.items():
            expect_list, enum_type = is_enum(field.annotation)
            if enum_type is None:
                continue
            value = getattr(self, key)
            if value is None:
                continue
            if isinstance(value, list) and expect_list:
                json_options[key] = [str(val) for val in value if val is not None]
                continue
            json_options[key] = str(value)
        return json_options


def get_model(temperature=0.75):
    client = AsyncOpenAI(
        base_url="http://localhost:1234/v1", api_key="lm-studio", max_retries=4
    )
    config = OpenAIConfig(
        "TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
        max_tokens=30000,
        temperature=temperature,
        user="Mario",
    )
    return openai(client, config)


def find_key_in_nested_dict(d, target_key):
    results = []

    def recursive_search(d):
        if isinstance(d, dict):
            for key, value in d.items():
                if key == target_key:
                    results.append(value)
                if isinstance(value, dict):
                    recursive_search(value)
                elif isinstance(value, list):  # In case the value is a list of dicts
                    for item in value:
                        if isinstance(item, dict):
                            recursive_search(item)

    recursive_search(d)
    return results


def return_modeled(cls_model: BaseModel, broken_json):
    def regex_clean_json(broken_json):
        return re.sub(r"```json(.*)```", r"\g<1>", re.sub(r"(\\n|\\)", "", broken_json))

    print(f"repairing model {cls_model} ...")
    if isinstance(broken_json, list):
        ext_json = "{" + ",".join([inp["input"] for inp in broken_json]) + "}"
        rep_json = repair_json(regex_clean_json(ext_json), return_objects=True)
        if rep_json:
            return cls_model.model_validate(rep_json)
    if isinstance(broken_json, str):
        rep_json = repair_json(regex_clean_json(broken_json))
        return cls_model.model_validate_json(rep_json)
    raise Exception("Invalid value to correct")


class JSONStreamingResponse(StreamingResponse, JSONResponse):
    """StreamingResponse that also render with JSON."""

    def __init__(
        self,
        content: Iterable | AsyncIterable,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> None:
        if isinstance(content, AsyncIterable):
            self._content_iterable: AsyncIterable = content
        else:
            self._content_iterable = iterate_in_threadpool(content)

        async def body_iterator() -> AsyncIterable[bytes]:
            async for content_ in self._content_iterable:
                if isinstance(content_, BaseModel):
                    content_ = content_.model_dump()
                yield self.render(content_)

        self.body_iterator = body_iterator()
        self.status_code = status_code
        if media_type is not None:
            self.media_type = media_type
        self.background = background
        self.init_headers(headers)
