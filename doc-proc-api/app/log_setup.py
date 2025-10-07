import logging


# from azure.monitor.opentelemetry import configure_azure_monitor

class CustomColoredFormatter(logging.Formatter):
    
    grey = '\x1b[38;21m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: blue + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
    

def setup_logger():
    
    from app.settings import get_settings
    app_settings = get_settings()
    
    # Create a logger
    logger = logging.getLogger()
    
    # Clear any existing handlers to prevent duplicates
    logger.handlers.clear()
    
    # Set logging level based on app_settings, default to INFO if empty or invalid
    log_level = getattr(app_settings, 'LOG_LEVEL', '').upper()
    if log_level == "DEBUG":
        logger.setLevel(logging.DEBUG)
    elif log_level == "WARNING":
        logger.setLevel(logging.WARNING)
    elif log_level == "ERROR":
        logger.setLevel(logging.ERROR)
    elif log_level == "CRITICAL":
        logger.setLevel(logging.CRITICAL)
    else:
        logger.setLevel(logging.INFO)
    
    # Only add handler if none exist
    if not logger.handlers:
        # Create a console handler and set the formatter
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(CustomColoredFormatter())

        # Add the console handler to the logger
        logger.addHandler(console_handler)
    
    
    # # Disable the App Insights VERY verbose logger
    logging.getLogger('azure.core').setLevel(logging.WARNING)
    # logging.getLogger('azure.identity').setLevel(logging.DEBUG if app_settings.DEBUG else logging.INFO)
    logging.getLogger('azure.identity').setLevel(logging.INFO)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)

    # # Configure OpenTelemetry to use Azure Monitor with the 
    # # APPLICATIONINSIGHTS_CONNECTION_STRING environment variable.
    # if APPLICATIONINSIGHTS_CONNECTION_STRING:
    #     configure_azure_monitor()
    # else:
    #     logger.warning("APPLICATIONINSIGHTS_CONNECTION_STRING is empty. Skipping Azure Monitor configuration.")
