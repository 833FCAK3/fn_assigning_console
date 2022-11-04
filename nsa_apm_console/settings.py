import yaml
from products_workflow.products.pga900 import Register

config = yaml.safe_load(open("settings.yml"))

# PARAMS
FN_REGISTER = Register.SensorNumber_int2

# URLS
LOGIN_URL = config["LOGIN_URL"]
LOGOUT_URL = config["LOGOUT_URL"]
PRODUCTS_URL = config["PRODUCTS_URL"]
ORDER_SEARCH_URL = config["ORDER_SEARCH_URL"]
GET_ORDER_URL = config["GET_ORDER_URL"]

# AUTH
API_KEY = config["API_KEY"]

PGA900_CONFIG = config["PGA900_CONFIG"]
