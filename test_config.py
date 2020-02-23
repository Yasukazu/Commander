import keepercommander.config as kcfg
import logging

config_dict = kcfg.set_by_json_file()
start_dict = kcfg.start()
logging_handlers = start_dict[kcfg.Logging]
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
for hdr in logging_handlers:
    logger.addHandler(hdr)
logger.info("Logger from 'test_config.py'.")
logging.info(f"Logging from {__name__}")