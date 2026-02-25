from pytest_bdd import scenarios

from steps.monitoring_steps import *

scenarios("features/monitoring/check_service_status.feature")
