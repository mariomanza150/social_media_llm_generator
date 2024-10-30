from typing import Any, Literal

from outlines import prompt
from pydantic import BaseModel, StringConstraints, field_serializer, model_validator
from styles import Style
from typing_extensions import Annotated


class Post(BaseModel):
    kind: str | BaseModel = "Generic"
    min: int = 30
    avg: int = 60
    max: int = 60
    text: str = None
    style: Style = None
    allowed_specials: list[str] = ["punctuation"]

    @field_serializer("style")
    def ser_enums(self, field_value, _info):
        return None if field_value is None else field_value.get_enum_names()


class XPost(Post):
    kind: str = "X (formerly Twitter)"
    min: int = 30
    avg: int = 60
    max: int = 140
    text: Annotated[str, StringConstraints(True, max_length=140)] = None
    allowed_specials: list[str] = ["punctuation", "hashtags", "emojis"]


class InstagramPost(Post):
    kind: str = "Instagram"
    length: int = 2200
    text: Annotated[str, StringConstraints(True, max_length=2200)] = None
    allowed_specials: list[str] = ["punctuation", "hashtags", "emojis"]


class FacebookPost(Post):
    kind: str = "Facebook"
    length: int = 63206
    text: Annotated[str, StringConstraints(True, max_length=63206)] = None
    allowed_specials: list[str] = ["punctuation", "hashtags", "emojis"]


class Platforms(BaseModel):
    name: Literal["generic", "x", "instagram", "facebook"] = "generic"
    post_model: Any = None

    @model_validator(mode="before")
    def load_post_model(cls, values):
        platform_mapping = {
            "x": XPost,
            "instagram": InstagramPost,
            "facebook": FacebookPost,
        }

        # Dynamically assign the model based on the platform name
        platform_name = values.get("name")
        model = platform_mapping.get(platform_name, Post)()
        values["post_model"] = model
        return values

    def get_post_model(self):
        post_instance = self.post_model()
        return post_instance


@prompt
def post_text(article, posts, platform, style):
    """\
    # CONTEXT #\

    ARTICLE:
        TITLE: {{ article.title }}
        DESCRIPTION: {{ article.description }}
        SUMMARY: {{ article.body }}

    GENERATED_POSTS: [{% for post in posts %}"{{ post.text }}",\n{% endfor %}]
        
    # OBJECTIVE #\

    Avoid repeating content from the GENERATED_POSTS list.
    Generate content for a social media post that comments on the article you just read.
    Tailor the content to {{ platform.kind }}.
    
    # STYLE #\

    - Post content should be generated using the following criteria:
        {% for key, value in style.items() %}
            {% if value %}
        - Stick to the following {{ key }} when writing:  {{ value }}.
            {% endif %}
        {% endfor %}
        - it should be tailored towards this platform: {{ platform.kind }}.
        - Write at least {{ platform.min }} characters.
        - Limit to {{ platform.max }} characters.
        - Use {{ platform.allowed_specials }} strategically to make the post content more appealing and expressive.

    # OUTPUT #
       A response that only contains the entire post content body.
    """
