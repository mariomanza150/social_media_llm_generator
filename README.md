# Social Media AI Generator

## What does this do?

Spins up a FastAPI server that allows users to fetch articles and generate social media content for Posts on that article. Several filters and options exist to refine the fetched articles and generated text from an LLM.

The idea is to help in the creation of social media content. Comments, Posts and Responses are planned, though Posts is the only one supported as of now.

Through a series of LLM calls with structured output, the LLM synthezises, determines writing style and generates a series of texts to Post on social media platforms.

In the future, implementing a RAG piece to write in a particular user's style would be great.

## Techstack

- Python, FastAPI, Outlines, Pydantic, Jinja2
- OpenAI / LLMs

## Prerequisites

- LLM Inference: Get a valid OpenAI api key, or setup LM Studio locally, set in `def get_model @ utils.py`
- TheNewsAPI: Currently, articles are fetched from [TheNewsAPI](https://www.thenewsapi.com/). You will need to create an account and retrieve an api key. set in `news_loader.py`

## Deployment

- Locally: Start the FastAPI server with `fastapi dev main.py`
- Production: (WIP)
