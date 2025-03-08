from urllib.parse import urlparse

from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers.html2text import Html2TextTransformer
from loguru import logger

from llm_enginerring.domain.documents import ArticleDocument

from .base import BaseCrawler

class CustomArticleCrawler(BaseCrawler):
    model = ArticleDocument

    def __init__(self) -> None:
        super().__init__()

    def extract(self, link:str, **kwargs) -> None:
        old_model = self.model.find(link=link)
        if old_model is not None:
            logger.info(f"Article already exists: {link}")

            return
        
        logger.info(f"Starting to scrape article: {link}")

        loader = AsyncHtmlLoader([link])
        docs = loader.load()

        html2text = Html2TextTransformer()
        docs_transformed = html2text.transform_documents(docs)
        docs_transformed = docs_transformed[0]
        ##logger.info(f"doc_transformed: {docs_transformed}")
        ##logger.info(f"doc_transform_raw: {docs_transformed.Document.metadata}")

        content = {
            "Title": docs_transformed.metadata.get("title"),
            "Subtitle": docs_transformed.metadata.get("description"),
            "Content": docs_transformed.page_content,
            "language": docs_transformed.metadata.get("language"),
        } 

        parsed_url = urlparse(link)
        platform = parsed_url.netloc

        user = kwargs["user"]
        instance = self.model(
            content=content,
            link=link,
            platform=platform,
            author_id=user.id,
            author_full_name=user.full_name,
        )
        instance.save()

        logger.info(f"Article crawled: {link}")