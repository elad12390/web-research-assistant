from pytest_bdd import scenarios

from steps.search_steps import *

scenarios("features/search/web_search.feature")
scenarios("features/search/search_examples.feature")
scenarios("features/search/search_images.feature")
