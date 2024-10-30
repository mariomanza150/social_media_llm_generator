from outlines import prompt
from pydantic import BaseModel, Field, field_serializer, model_validator
from pydantic_core import ValidationError
from typing_extensions import Annotated, Any, Optional
from utils import Choices, Option


class GenChoices(Choices):
    def as_jsonable(self):
        return {"value": self.name, "text": self.name.replace("_", " ").title()}


class AudienceChoice(GenChoices):
    general = "intended for a broad, non-specialized audience."
    professionals = "targeting individuals with specialized knowledge or expertise in a particular field."
    students = "aimed at learners, with content simplified for educational purposes."
    academics = "written for scholars or researchers, using formal language and possibly citations."
    enthusiasts = (
        "intended for hobbyists or people with a deep interest in a specific topic."
    )
    customers = "addressing individuals who are current or potential buyers of a product or service."
    executives = "crafted for C-level professionals, focusing on high-level strategy or decision-making."
    technical_staff = "targeted at individuals with technical or engineering expertise."
    stakeholders = "meant for individuals or groups who have a vested interest in a project or outcome."


class PurposeChoice(GenChoices):
    invite = "invites to read and discuss the topic."
    inform = (
        "provides information or explanations without trying to persuade the reader."
    )
    persuade = (
        "aims to convince the reader to adopt a particular viewpoint or take action."
    )
    entertain = (
        "designed to engage the reader with humor, stories, or engaging content."
    )
    educate = "intends to teach the reader something new, possibly through a structured lesson or guide."
    inspire = "seeks to motivate the reader to think or act differently."
    sell = "tries to convince the reader to purchase a product or service."
    critique = (
        "analyzes and evaluates something, pointing out strengths and weaknesses."
    )


class LengthPreferenceChoice(GenChoices):
    concise = "keeps the post short and to the point, focusing on brevity."
    balanced = "provides a moderate length, balancing detail and conciseness."
    detailed = (
        "offers an in-depth, comprehensive post, covering the topic in great detail."
    )


class VoiceChoice(GenChoices):
    first_person = "written from the author's perspective, using 'I' or 'we'."
    second_person = "addresses the reader directly, using 'you'."
    third_person = "written in a neutral tone, referring to people as 'he', 'she', 'they', or 'it'."


class PositionChoice(GenChoices):
    strongly_agree = "fully supports the argument or opinion."
    agree = "generally agrees with some minor reservations."
    neutral = "takes no strong stance, acknowledging both sides."
    disagree = "generally disagrees but recognizes some valid points."
    strongly_disagree = "fully opposes the argument or opinion."
    critique = "analyzes the argument, pointing out weaknesses."
    challenge = "questions the logic or assumptions behind the argument."
    alternative_perspective = "offers a different viewpoint from the original argument."
    expand = "agrees and adds further ideas or evidence."
    clarify = "offers clarification or explanation of the original stance."


class ToneChoice(GenChoices):
    formal = (
        "uses formal language and tone, suitable for professional or academic settings."
    )
    informal = "relaxed, conversational tone, possibly using slang or contractions."
    authoritative = (
        "confident and assertive, often providing expert advice or judgment."
    )
    empathetic = (
        "conveys understanding and emotional sensitivity to the reader's feelings."
    )


class Style(Option):
    audience: Optional[AudienceChoice] = None
    purpose: Optional[PurposeChoice] = None
    length_preference: Optional[LengthPreferenceChoice] = None
    voice: Optional[VoiceChoice] = None
    position: Optional[PositionChoice] = None
    tone: Optional[ToneChoice] = None

    @field_serializer(
        "audience", "purpose", "length_preference", "voice", "position", "tone"
    )
    def ser_enums(self, field_value, _info):
        return None if field_value is None else field_value.name


class Styles(BaseModel):
    styles: Annotated[
        list[Style],
        Field(
            default=[
                Style(
                    audience=AudienceChoice["general"],
                    purpose=PurposeChoice["invite"],
                    length_preference=LengthPreferenceChoice["balanced"],
                    voice=VoiceChoice["third_person"],
                    position=PositionChoice["neutral"],
                    tone=ToneChoice["formal"],
                )
            ],
            min_items=1,
        ),
    ]

    @model_validator(mode="before")
    @classmethod
    def handle_structure(cls, values: Any) -> Any:
        styles = []

        if isinstance(values, list):
            for val in values:
                if isinstance(val, dict):
                    try:
                        styles.append(Style(**val))
                    except ValidationError as e:
                        print(e)
                        run_again = cls.model_validate(val)
                        if run_again is not None:
                            for style in run_again.styles:
                                styles.append(style)
                elif isinstance(val, list):
                    for item in val:
                        run_again = cls.model_validate(item)
                        if run_again is not None:
                            for style in run_again.styles:
                                styles.append(style)

        elif isinstance(values, dict) and len(values) > 1:
            if all([isinstance(val, str) for val in values.values()]):
                styles.append(Style(**values))
            else:
                for key, item in values.items():
                    run_again = cls.model_validate(val)
                    if run_again is not None:
                        for style in run_again.styles:
                            styles.append(style)
        elif isinstance(values, dict) and "styles" in values:
            for val in values["styles"]:
                if isinstance(val, dict):
                    try:
                        styles.append(Style(**val))
                    except Exception as e:
                        print(e)
                        styles.append(cls.model_validate(values))
                elif isinstance(val, Style):
                    styles.append(val)

        if len(styles) > 0:
            return {"styles": styles}


@prompt
def style_selection(
    article,
    cons_styles,
    count=5,
    eg=Styles(
        styles=[
            Style(
                audience=AudienceChoice.general,
                purpose=PurposeChoice.invite,
                position=PositionChoice.neutral,
            ),
            Style(
                position=PositionChoice.agree,
                tone=ToneChoice.formal,
                length_preference=LengthPreferenceChoice.balanced,
            ),
        ]
    ).model_dump_json(),
):
    """
    # CONTEXT #
    ARTICLE:
        TITLE: "{{ article.title }}"
        DESCRIPTION: "{{ article.description }}"
        SUMMARY: "{{ article.body }}"

    # OBJECTIVE #
    Determine a set of Styles to use when writing a post on social media about an article (ARTICLE).
    Repeat the following {{ count }} times:
        Construct a Style to write a post, choose from the following options:
           {% for key, value in cons_styles.items() %}
               - "{{ key }}": {{ value }}
           {% endfor %}
        Find harmony in the Style you choose.

    # OUTPUT #
    Respond only with a JSON containing a single "styles" key.
    Format your response as a list of {{ count }} dictionaries.
    Example JSON output:
    {{ eg }}
    """
