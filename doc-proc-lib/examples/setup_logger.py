import logging
from colorama import Fore, Style, init

def setup_logging():
    """Setup logging configuration."""
    
    # Clear any existing handlers to prevent duplicates
    # Create a logger
    logger = logging.getLogger()
    logger.handlers.clear()
    
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    class ColorFormatter(logging.Formatter):
        COLORS = {
            logging.DEBUG: Fore.CYAN,
            logging.INFO: Fore.GREEN,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.RED + Style.BRIGHT,
        }
        def format(self, record):
            color = self.COLORS.get(record.levelno, "")
            message = super().format(record)
            return f"{color}{message}{Style.RESET_ALL}"

    formatter = ColorFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)')
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)
    
    logging.getLogger('azure.core').setLevel(logging.WARNING)
    logging.getLogger('azure.identity').setLevel(logging.INFO)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)