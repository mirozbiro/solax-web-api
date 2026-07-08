from datetime import timedelta

DOMAIN = "solax_export_control"
INTEGRATION_VERSION = "0.1.3"

PLATFORMS = ["number", "sensor", "button"]

CONF_SN = "sn"
CONF_INVERTER_SN = "inverter_sn"
CONF_TOKEN_ID = "token_id"
CONF_PIN = "pin"
CONF_MIN_EXPORT_W = "min_export_w"
CONF_MAX_EXPORT_W = "max_export_w"

DEFAULT_NAME = "Solax Export Control"
DEFAULT_MIN_EXPORT_W = 0
DEFAULT_MAX_EXPORT_W = 10000
DEFAULT_SCAN_INTERVAL = timedelta(hours=1)

REG_EXPORT_LIMIT = 48
REG_PIN = 0

ATTR_EXPORT_LIMIT_W = "export_limit_w"
ATTR_LAST_UPDATE_SUCCESS = "last_update_success"
ATTR_LAST_ERROR = "last_error"
