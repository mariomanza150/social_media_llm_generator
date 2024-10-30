import re

import requests
from bs4 import BeautifulSoup
from outlines import generate
from posts import Platforms, Post, post_text
from pydantic_core import ValidationError
from styles import Style, Styles, style_selection
from summary import Summaries, chain_of_density
from utils import get_model, return_modeled


class Orchestrator:
    article = {"uuid": ""}

    def _get_article_body(self, url):
        org_article = requests.get(
            url,
            allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
                "X-Requested-With": "XMLHTTPSRequest",
            },
            timeout=15,
        )
        art_body = BeautifulSoup(org_article.text, "html.parser").get_text()

        return (
            re.sub(r"\s+", " ", art_body.lower())
            .replace("“", "'")
            .replace("”", "'")
            .replace('"', "'")
        )

    def _summarize(self, article):
        article["body"] = self._get_article_body(article["url"])
        prompt = chain_of_density(article)
        try:
            generator = generate.json(get_model(), Summaries)
            summaries = generator(prompt)
        except ValidationError as e:
            summaries = return_modeled(Summaries, e.errors())
        print("summed up")
        return "\n".join([summary.Denser_Summary for summary in summaries.summaries])

    def _style(self, prompt):
        try:
            style_selector = generate.json(get_model(0.8), Styles)
            return style_selector(prompt)
        except ValidationError as e:
            print("style error, trying to model")
            return return_modeled(Styles, e.errors())

    def _get_styles(self, summaries, cons_style: Style):
        print("recieved style: ", cons_style)
        styles = Style.get_options()
        if cons_style is not None:
            for key, _ in styles.items():
                cons = getattr(cons_style, key, None)
                if cons is not None:
                    styles[key] = [cons]
        if any([len(opts) > 1 for _, opts in styles.items()]):
            print("determining style options")
            prompt = style_selection(summaries, {**styles})
            print("\nStyle prompt", prompt, "\n")
            return self._style(prompt)
        return Styles(styles=[cons_style])

    def _gen_post_text(self, prompt):
        try:
            post_generator = generate.text(get_model(1.6))
            text = post_generator(prompt)
            print("generated post")
            return text
        except Exception as e:
            print("error while gen post", e)
            return self._gen_post(prompt)

    def _write_posts(self, article, target: Platforms, styles: Styles):
        posts = []
        for idx in range(5):
            style = (
                styles.styles[idx] if len(styles.styles) > idx else styles.styles[-1]
            )
            prompt = post_text(article, posts, target.post_model, style.get_enums())
            print("\nPost prompt", prompt, "\n")
            text = self._gen_post_text(prompt)

            post = {
                "text": text,
                "style": style,
            }
            post = Post(**post)
            posts.append(post)
            yield post

    def generate(self, article, style: Style, target: str):
        print("generating")
        target = Platforms(name=target)
        print("platform", target)

        if self.article["uuid"] == article["uuid"]:
            article = self.article
        else:
            yield {"event": "reading_article"}
            article["body"] = self._summarize(article)
            self.article = article

        yield {"event": "determining_styles"}
        styles = self._get_styles(article, style)
        print(styles)
        yield {"event": "writing_posts"}

        for post in self._write_posts(article, target, styles):
            yield {
                "event": "post_created",
                "data": {"post": post.model_dump_json()},
            }
