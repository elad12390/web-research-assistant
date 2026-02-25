from pytest_bdd import scenarios

from steps.packages_steps import *

scenarios("features/packages/package_info.feature")
scenarios("features/packages/package_search.feature")
scenarios("features/packages/get_changelog.feature")
