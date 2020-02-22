import keepercommander.config as kcfg
import logging

kcfg.set_by_json_file()
kcfg.start()
logger = logging.getLogger(__name__)
logging.info("Logging from 'test_config.py'.")
