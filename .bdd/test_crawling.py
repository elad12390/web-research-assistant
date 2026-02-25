from pytest_bdd import scenarios

from steps.crawling_steps import *

scenarios("features/crawling/crawl_url.feature")
scenarios("features/crawling/extract_data.feature")
