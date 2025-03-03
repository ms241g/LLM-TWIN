from urllib.parse import urlparse

from loguru import logger
from tqdm import tqdm
from typing_extensions import Annotated
from zenml import get_step_context, step

from llm_enginerring.application.crawlers.dispatcher import CrawlerDispatcher
from llm_enginerring.domain.documents import UserDocument

@step
def crawl_links(user: UserDocument, links: list[str]) -> Annotated[list[str], "crawled_links"]:
    dispatcher = CrawlerDispatcher.build().register_linkedin().register_medium().register_github()

    logger.info(f"Starting to crawl {len(links)} link(s).")

    metadata = {}
    successfull_crawls = 0
    logger.info("links: ", links)
    for link in tqdm(links):
        print("Link: ", link)
        successfull_crawl, crawled_domain = _crawl_link(dispatcher, link, user)
        successfull_crawls += successfull_crawl

        metadata = _add_to_metadata(metadata, crawled_domain, successfull_crawl)
        logger.info("metadata: ", metadata)

    step_context = get_step_context()
    step_context.add_output_metadata(output_name="crawled_links", metadata=metadata)

    logger.info(f"Successfully crawled {successfull_crawls} / {len(links)} links.")

    return links


def _crawl_link(dispatcher: CrawlerDispatcher, link: str, user: UserDocument) -> tuple[bool, str]:
    crawler = dispatcher.get_crawler(link)
    logger.info("After getting the crawler from dispatcher")
    crawler_domain = urlparse(link).netloc
    logger.info("After getting the crawler domain")
    

    try:
        crawler.extract(link=link, user=user)

        return (True, crawler_domain)
    except Exception as e:
        logger.error(f"An error occurred while crawling: {e!s}")

        return (False, crawler_domain)


def _add_to_metadata(metadata: dict, domain: str, successfull_crawl: bool) -> dict:
    if domain not in metadata:
        metadata[domain] = {}
    metadata[domain]["successful"] = metadata.get(domain, {}).get("successful", 0) + successfull_crawl
    metadata[domain]["total"] = metadata.get(domain, {}).get("total", 0) + 1

    return metadata