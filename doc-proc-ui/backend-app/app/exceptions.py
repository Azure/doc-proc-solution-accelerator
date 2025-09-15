import fastapi
import logging
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger("doc-proc-ui.app.exceptions")

class ServiceException(Exception):
    
    def __init__(self, message, service_name):
        Exception.__init__(self)
        self.message = message
        self.service_name = service_name


class ApiException(Exception):
    default_status_code = 500
    status_messages = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        406: "Not Acceptable",
        409: "Conflict",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
    }

    def __init__(self, message, status_code=None, details:str=None):
        
        Exception.__init__(self)
        self.message = message
        self.details = details

        # Set the status code or default to 500
        self.status_code = (
            status_code if status_code is not None else self.default_status_code
        )


async def api_exception_handler(request: fastapi.Request, exc: ApiException) -> JSONResponse:
        logger.error(f"❌ Api Error: {str(exc)}")
        logger.exception(exc)
        
        return JSONResponse(
             status_code=exc.status_code, 
             content={"message": "❌ Api Error", "error": exc.message, "details": exc.details}
        )


async def validation_exception_handler(request: fastapi.Request, exc: ValidationError):
        logger.error(f"❌ Unhandled Validation Error: {str(exc)}")
        logger.exception(exc)

        return JSONResponse(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"message": "❌ Model Validation Error", "error": exc.json()}
        )


async def all_other_exceptions_handler_middleware(request: fastapi.Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error(f"❌ Unhandled Error: {str(exc)}")
        logger.exception(exc)

        return JSONResponse(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "❌ Internal Server Error", "error": str(exc)}
        )
            

def add_exception_handlers(app: fastapi.FastAPI):
    
    logging.info("Adding exception handlers to the application")

    # this handles the ApiException raised by the application, it should return the status code and the error message
    # to the client
    app.add_exception_handler(ApiException, api_exception_handler)
    
    # this handles the model validation on lower levels, it is responsible for business logic validation
    # and it should return 422 as status code. we return generic error message to the client and log the error
    app.add_exception_handler(ValidationError, validation_exception_handler)

    app.middleware('http')(all_other_exceptions_handler_middleware)