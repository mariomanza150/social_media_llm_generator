import requests

from news_filters import NewsFilter


class NewsLoader:
    def __init__(self, news_filter: NewsFilter = NewsFilter()) -> None:
        news_filter.locale = "us"
        news_filter.language = "en"
        self.news_filter = news_filter

    def _apply_filters(self):
        pass

    def _update_filter(self):
        pass

    def _get_page(self):
        pass

    def get_news(self, news_filter: NewsFilter = None):
        if news_filter is not None:
            self.news_filter = news_filter
        if self.news_filter.page > 19999:
            raise ValueError("Page Limit Reached")

        url = "https://api.thenewsapi.com/v1/news/"
        url += "top" if news_filter.top else "all"

        param_dump = news_filter.model_dump(exclude_defaults=True, exclude_unset=True)

        fetch = requests.get(
            "https://api.thenewsapi.com/v1/news/all",
            auth=("api_token", ""),
            params=param_dump,
        ).json()

        if "error" in fetch:
            return []
    
        f_data = fetch["meta"]
        self.news_filter.count = f_data["found"]
        f_news = fetch["data"]
        return f_news
