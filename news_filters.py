from typing import Optional

from pydantic import Field, NaiveDatetime, field_serializer
from utils import Choices, Option


class LocaleChoice(Choices):
    ar = "Argentina"
    am = "Armenia"
    au = "Australia"
    at = "Austria"
    by = "Belarus"
    be = "Belgium"
    bo = "Bolivia"
    br = "Brazil"
    bg = "Bulgaria"
    ca = "Canada"
    cl = "Chile"
    cn = "China"
    co = "Colombia"
    hr = "Croatia"
    cz = "Czechia"
    ec = "Ecuador"
    eg = "Egypt"
    fr = "France"
    de = "Germany"
    gr = "Greece"
    hn = "Honduras"
    hk = "Hong Kong"
    ind = "India"
    id = "Indonesia"
    ir = "Iran"
    ie = "Ireland"
    il = "Israel"
    it = "Italy"
    jp = "Japan"
    kr = "Korea"
    mx = "Mexico"
    nl = "Netherlands"
    nz = "New Zealand"
    ni = "Nicaragua"
    pk = "Pakistan"
    pa = "Panama"
    pe = "Peru"
    pl = "Poland"
    pt = "Portugal"
    qa = "Qatar"
    ro = "Romania"
    ru = "Russia"
    sa = "Saudi Arabia"
    za = "South Africa"
    es = "Spain"
    ch = "Switzerland"
    sy = "Syria"
    tw = "Taiwan"
    th = "Thailand"
    tr = "Turkey"
    ua = "Ukraine"
    gb = "United Kingdom"
    us = "United States Of America"
    uy = "Uruguay"
    ve = "Venezuela"


class LanguageChoice(Choices):
    ar = "Arabic"
    bg = "Bulgarian"
    bn = "Bengali"
    cs = "Czech"
    da = "Danish"
    de = "German"
    el = "Greek"
    en = "English"
    es = "Spanish"
    et = "Estonian"
    fa = "Persian"
    fi = "Finnish"
    fr = "French"
    he = "Hebrew"
    hi = "Hindi"
    hr = "Croatian"
    hu = "Hungarian"
    id = "Indonesian"
    it = "Italian"
    ja = "Japanese"
    ko = "Korean"
    lt = "Lithuanian"
    multi = "Multiple Languages"
    nl = "Dutch"
    no = "Norwegian"
    pl = "Polish"
    pt = "Portuguese"
    ro = "Romanian"
    ru = "Russian"
    sk = "Slovak"
    sv = "Swedish"
    ta = "Tamil"
    th = "Thai"
    tr = "Turkish"
    uk = "Ukrainian"
    vi = "Vietnamese"
    zh = "Chinese"


class CategoryChoice(Choices):
    general = "General"
    science = "Science"
    sports = "Sports"
    business = "Business"
    health = "Health"
    entertainment = "Entertainment"
    tech = "Technology"
    politics = "Politics"
    food = "Food"
    travel = "Travel"


class NewsFilter(Option):
    locale: list[LocaleChoice] = None
    language: list[LanguageChoice] = None
    categories: list[CategoryChoice] = None
    published_before: Optional[NaiveDatetime] = None
    published_after: Optional[NaiveDatetime] = None
    published_on: Optional[NaiveDatetime] = None
    top: bool = Field(default=True)
    page: int = Field(default=1)
    count: int = Field(default=0)

    @field_serializer("locale", "language", "categories")
    def ser_enums(self, field_value, _info):
        return [val.name for val in field_value if field_value is not None]
