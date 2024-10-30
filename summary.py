from outlines import prompt
from pydantic import BaseModel, model_validator
from pydantic.types import conlist
from pydantic_core import ValidationError
from utils import find_key_in_nested_dict


class Summary(BaseModel):
    Missing_Entities: str | list[str] = []
    Denser_Summary: str


class Summaries(BaseModel):
    summaries: conlist(Summary, max_length=5, min_length=1)  # type: ignore

    @model_validator(mode="before")
    @classmethod
    def handle_structure(cls, values):
        if isinstance(values, dict) and len(values) > 1:
            found = []
            for elem in find_key_in_nested_dict(values, "summaries"):
                if isinstance(elem, dict):
                    try:
                        style = Summary(**elem)
                        found.append(style)
                    except ValidationError:
                        pass
                if isinstance(elem, list):
                    for item in elem:
                        if isinstance(item, dict):
                            try:
                                style = Summary(**item)
                                found.append(style)
                            except ValidationError:
                                pass
            return {"summaries": found}
        if isinstance(values, list):
            values = {"summaries": values[:5]}
        return values


@prompt
def chain_of_density(article):
    """Article:
        TITLE: {{ article.title }}
        DESCRIPTION: {{ article.description }}
        SNIPPET: {{ article.snippet }}
        BODY: {{ article.body }}

    You will generate increasingly concise, entity-dense summaries of the above Article.

    Repeat the following 2 steps 5 times.

    Step 1. Identify 1-3 informative Entities ("; " delimited) from the Article which are missing from the previously generated summary.
    Step 2. Write a new, denser summary of identical length which covers every entity and detail from the previous summary plus the Missing Entities.

    A Missing Entity is:
    - Relevant: to the main story.
    - Specific: descriptive yet concise (5 words or fewer).
    - Novel: not in the previous summary.
    - Faithful: present in the Article.
    - Anywhere: located anywhere in the Article.

    Guidelines:
    - The first summary should be long (4-5 sentences, ~80 words) yet highly non-specific, containing little information beyond the entities marked as missing. Use overly verbose language and fillers (e.g., "this article discusses") to reach ~80 words.
    - Make every word count: rewrite the previous summary to improve flow and make space for additional entities.
    - Make space with fusion, compression, and removal of uninformative phrases like "the article discusses".
    - The summaries should become highly dense and concise yet self-contained, e.g., easily understood without the Article.
    - Missing entities can appear anywhere in the new summary.
    - Never drop entities from the previous summary. If space cannot be made, add fewer new entities.

    # OUTPUT #
    Answer only in valid JSON. The JSON should be a a dictionary with key "summaries" that contains a list (length 5) of dictionaries whose keys are "Missing_Entities" and "Denser_Summary".
    EXAMPLE OUTPUT: {
        "summaries": ["Missing_Entities": [], "Denser_Summary": ""]
    }
    """
