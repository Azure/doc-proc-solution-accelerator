"""
Provides dependencies for API calls.
"""
import logging
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from configuration import Configuration

__config: Configuration = None

def get_config(action: str = None) -> Configuration:
    global __config

    if action is not None and action=='refresh':
        __config = Configuration()
    else:
        __config = __config or Configuration()
    return __config

def validate_api_key_header(x_api_key: str = Depends(APIKeyHeader(name='X-API-Key'))):
    result = x_api_key == get_config().get_value(f'INGEST_APP_APIKEY')
    
    if not result:
        logging.error('Invalid API key. You must provide a valid API key in the X-API-KEY header.')
        raise HTTPException(
            status_code = 401,
            detail = 'Invalid API key. You must provide a valid API key in the X-API-KEY header.'
        )

def handle_exception(exception: Exception, status_code: int = 500):
    logging.error(exception, stack_info=True, exc_info=True)
    raise HTTPException(
        status_code = status_code,
        detail = str(exception)
    ) from exception
