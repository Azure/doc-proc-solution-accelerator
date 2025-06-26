import logging

from .blob_service import BlobService
from .service_base import ServiceBase

logger = logging.getLogger(__name__)


async def get_blob_service(name:str, type:str, settings: dict) -> BlobService:
    """
    Get an instance of BlobService using the provided settings.
    """

    logger.debug(f"Creating BlobService instance: {name}.")
    
    async with BlobService(name=name, type=type, **settings) as blob_service:
        return blob_service


async def get_service(name:str, type:str, settings: dict) -> ServiceBase:
    """Get an instance of the specified service type."""

    logger.debug(f"Creating service instance: {name} of type: {type}.")

    if type == 'azure_blob':
        return await get_blob_service(name=name, type=type, settings=settings)

    raise ValueError(f"Unknown service type: {type}")