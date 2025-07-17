import logging
from typing import List
from enum import Enum
from pathlib import Path

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig

logger = logging.getLogger("doc.proc.step.document_type_identifier")


class DocumentCategory(Enum):
    OFFICE_DOCUMENT = "office_document"
    PDF = "pdf"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    TEXT = "text"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    EMAIL = "email"
    WEB = "web"
    EXECUTABLE = "executable"
    UNKNOWN = "unknown"

class IdentificationMethod(Enum):
    MAGIC_BYTES = "magic_bytes"
    FILE_EXTENSION = "file_extension"


class DocumentTypeIdentifierStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        # Extract configuration settings
        methods = self.settings.get("identification_methods", "magic_bytes, file_extension")

        self.identification_methods = [IdentificationMethod(m.strip()) for m in methods.split(",")]

        logger.debug(f"Initialized DocumentTypeIdentifierStep with identification_methods: {self.identification_methods}")


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        """
        Identify document types and formats for input documents.
        
        Args:
            input_data: Input containing dict of documents to analyze
            context: Pipeline execution context
            
        Returns:
            StepInputOutput: Output with type identification results
        """

        # Check if input_data has the required data structure
        if not input_data or not isinstance(input_data, StepInputOutput) or not hasattr(input_data, 'data') or input_data.data is None:
            logger.error(f"Invalid input data: {input_data}. Expected StepInputOutput instance.")
            raise StepExecutionError(f"Invalid input data: {input_data}. Expected StepInputOutput instance.")
        
        _stats = {
            "total_documents": 0,
            "successful_documents": 0,
            "failed_documents": 0
        }

        # get documents from input data
        documents = input_data.data.get("documents", [])
        if not documents or not isinstance(documents, list):
            logger.warning(f"No documents found in input data: {input_data.data}. Expected a list of documents.")
            # do nothing if no documents are found
            return StepInputOutput(summary_data={
                                        **input_data.summary_data, f"{self.name}_stats": _stats
                                   },
                                   data={
                                       **input_data.data
                                   })

        # Iterate through each document in the input data
        logger.info(f"Processing {len(documents)} documents...")

        _stats["total_documents"] = len(documents)

        final_documents_list = []

        for document in documents:
            try:

                if self.debug_mode:
                    logger.debug(f"Processing document: {document}")
                

                document_dict = document if isinstance(document, dict) else {"file_path": document}
                if not isinstance(document_dict, dict) or "file_path" not in document_dict:
                    raise ValueError(f"Invalid document format: {document}. Expected a dictionary with 'file_path' key.")

                # Process the file based on identification methods
                identification_result = await self.process_document(
                    document_dict, self.identification_methods
                )

                result_document = {
                    **document_dict,
                    "document_type": identification_result,
                }

                _stats["successful_documents"] += 1

                final_documents_list.append(result_document)

            except Exception as e:
                logger.error(f"Error processing document {document}: {e}")
                _stats["failed_documents"] += 1

                if self.fail_step_on_document_error:
                    # If the step is configured to fail on document error, raise an exception
                    raise StepExecutionError(f"Failed to process document {document}: {e}")


        # Return the updated StepInputOutput
        return StepInputOutput(summary_data = {**input_data.summary_data, f"{self.name}_stats": _stats}, 
                               data={**input_data.data, "documents": final_documents_list})


    async def process_document(self, document: dict, 
                                     identification_methods: List[IdentificationMethod]) -> dict:
        """Process a document for type identification"""
        if not document or not isinstance(document, dict):
            raise ValueError("Invalid document format. Expected a dictionary with file metadata.")
        
        try:
            # Perform document type identification
            identification_result = await self.identify_document_type(
                document, identification_methods
            )

            return identification_result
                
        except Exception as e:
                logger.error(f"Document type identification failed for {document.get('id', 'unknown')}: {str(e)}")
                raise ValueError(f"Document type identification failed: {str(e)}")


    async def identify_document_type(self, document: dict, 
                                           identification_methods: List[IdentificationMethod]) -> dict:
        """Perform comprehensive document type identification"""
        identification_results = {}
        
        # Method 1: Magic bytes detection
        if IdentificationMethod.MAGIC_BYTES in identification_methods:
            magic_result = await self.identify_by_magic_bytes(document)
            identification_results["magic_bytes"] = magic_result
        
        # Method 2: File extension analysis
        if IdentificationMethod.FILE_EXTENSION in identification_methods:
            
            extension_result = await self.identify_by_file_extension(document)
            identification_results["file_extension"] = extension_result
        
        # Combine and rank results
        final_identification = await self.combine_identification_results(
            identification_results
        )
        
        return final_identification
    
    async def identify_by_magic_bytes(self, document: dict) -> dict:
        """Identify document type using magic bytes/file signatures"""
        
        import magic
        
        try:
            logger.debug(f"Identifying document by magic bytes: {document.get('file_path', 'unknown')}")

            file_path = document.get("file_path", "")
            if not file_path:
                return {"error": "No file path available", "confidence": 0.0, "method": "magic_bytes"}
            # Read the file content
            if not Path(file_path).is_file():
                return {"error": f"File not found: {file_path}", "confidence": 0.0, "method": "magic_bytes"}

            with open(file_path, "rb") as f:
                file_content = f.read()

            if isinstance(file_content, str):
                file_content = file_content.encode()
            
            # Use python-magic library for magic bytes detection
            mime_type = magic.from_buffer(file_content, mime=True)
            file_type = magic.from_buffer(file_content)
            
            return {
                "mime_type": mime_type,
                "type": file_type,
                "confidence": 0.95,
                "method": "magic_bytes"
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "confidence": 0.0,
                "method": "magic_bytes"
            }
    
    async def identify_by_file_extension(self, document: dict) -> dict:
        """Identify document type using file extension"""
        
        try:
            logger.debug(f"Identifying document by file extension: {document.get('file_path', 'unknown')}")

            file_path = document.get("file_path", "")
            if not file_path:
                return {"error": "No file path available", "confidence": 0.0, "method": "file_extension"}

            # Check if file exists
            if not Path(file_path).is_file():
                return {"error": f"File not found: {file_path}", "confidence": 0.0, "method": "file_extension"}

            # Extract extension
            file_path = Path(file_path)
            extension = file_path.suffix.lower()
            
            # Map extensions to document types
            extension_mapping = {
                ".pdf": {"type": "pdf", "mime_type": "application/pdf", "subtype": "pdf", "category": DocumentCategory.PDF.value},
                ".docx": {"type": "word_document", "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "subtype": "openxml", "category": "office_document"},
                ".doc": {"type": "word_document", "mime_type": "application/msword", "subtype": "legacy", "category": "office_document"},
                ".xlsx": {"type": "excel_spreadsheet", "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "subtype": "openxml", "category": "spreadsheet"},
                ".xls": {"type": "excel_spreadsheet", "mime_type": "application/vnd.ms-excel", "subtype": "legacy", "category": "spreadsheet"},
                ".pptx": {"type": "powerpoint_presentation", "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation", "subtype": "openxml", "category": "presentation"},
                ".ppt": {"type": "powerpoint_presentation", "mime_type": "application/vnd.ms-powerpoint", "subtype": "legacy", "category": "presentation"},
                ".txt": {"type": "text_document", "mime_type": "text/plain", "subtype": "plain_text", "category": "text"},
                ".rtf": {"type": "rich_text", "mime_type": "application/rtf", "subtype": "rtf", "category": "text"},
                ".odt": {"type": "openoffice_document", "mime_type": "application/vnd.oasis.opendocument.text", "subtype": "text", "category": "office_document"},
                ".ods": {"type": "openoffice_spreadsheet", "mime_type": "application/vnd.oasis.opendocument.spreadsheet", "subtype": "calc", "category": "spreadsheet"},
                ".odp": {"type": "openoffice_presentation", "mime_type": "application/vnd.oasis.opendocument.presentation", "subtype": "impress", "category": "presentation"},
                ".jpg": {"type": "image", "mime_type": "image/jpeg", "subtype": "jpeg", "category": "image"},
                ".jpeg": {"type": "image", "mime_type": "image/jpeg", "subtype": "jpeg", "category": "image"},
                ".png": {"type": "image", "mime_type": "image/png", "subtype": "png", "category": "image"},
                ".gif": {"type": "image", "mime_type": "image/gif", "subtype": "gif", "category": "image"},
                ".bmp": {"type": "image", "mime_type": "image/bmp", "subtype": "bitmap", "category": "image"},
                ".tiff": {"type": "image", "mime_type": "image/tiff", "subtype": "tiff", "category": "image"},
                ".svg": {"type": "image", "mime_type": "image/svg+xml", "subtype": "svg", "category": "image"},
                ".html": {"type": "web_document", "mime_type": "text/html", "subtype": "html", "category": "web"},
                ".htm": {"type": "web_document", "mime_type": "text/html", "subtype": "html", "category": "web"},
                ".xml": {"type": "structured_document", "mime_type": "application/xml", "subtype": "xml", "category": "text"},
                ".json": {"type": "data_document", "mime_type": "application/json", "subtype": "json", "category": "text"},
                ".csv": {"type": "data_document", "mime_type": "text/csv", "subtype": "csv", "category": "text"},
                ".zip": {"type": "archive", "mime_type": "application/zip", "subtype": "zip", "category": "archive"},
                ".rar": {"type": "archive", "mime_type": "application/x-rar-compressed", "subtype": "rar", "category": "archive"},
                ".7z": {"type": "archive", "mime_type": "application/x-7z-compressed", "subtype": "7zip", "category": "archive"},
                ".tar": {"type": "archive", "mime_type": "application/x-tar", "subtype": "tar", "category": "archive"},
                ".gz": {"type": "archive", "mime_type": "application/gzip", "subtype": "gzip", "category": "archive"}
            }
            
            if extension in extension_mapping:
                result = extension_mapping[extension]
                result.update({
                    "extension": extension,
                    "confidence": 0.9,
                    "method": "file_extension"
                })
                return result
            else:
                return {
                    "extension": extension,
                    "type": "unknown",
                    "confidence": 0.0,
                    "method": "file_extension"
                }


        except Exception as e:
            return {
                "error": str(e),
                "confidence": 0.0,
                "method": "file_extension"
            }
        
    async def combine_identification_results(self, results: dict) -> dict:
        """Combine multiple identification results into final determination"""
        if not results:
            return {"primary_type": "unknown", "confidence": 0.0}
        
        # Weight different methods by reliability
        method_weights = {
            "magic_bytes": 0.95,
            "file_extension": 0.9
        }
        
        weighted_results = []
        for method, result in results.items():
            if "error" not in result:
                weight = method_weights.get(method, 0.5)
                confidence = result.get("confidence", 0.0)
                weighted_confidence = confidence * weight
                
                weighted_results.append({
                    "method": method,
                    "result": result,
                    "weighted_confidence": weighted_confidence
                })
        
        if not weighted_results:
            return {"primary_type": "unknown", "confidence": 0.0}
        
        # Sort by weighted confidence
        weighted_results.sort(key=lambda x: x["weighted_confidence"], reverse=True)
        
        best_result = weighted_results[0]
        
        # Create final identification result
        final_result = {
            "primary_type": best_result["result"].get("type", "unknown"),
            "mime_type": best_result["result"].get("mime_type", "unknown"),
            "confidence": best_result["weighted_confidence"],
            "best_method": best_result["method"],
            "all_methods": {method: result for method, result in results.items()}
        }
        
        # Add additional details if available
        if "subtype" in best_result["result"]:
            final_result["subtype"] = best_result["result"]["subtype"]
        if "category" in best_result["result"]:
            final_result["category"] = best_result["result"]["category"]
        
        return final_result