import logging
from typing import List
from enum import Enum
import magic
import mimetypes
from pathlib import Path

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput

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
    CONTENT_ANALYSIS = "content_analysis"
    AI_CLASSIFICATION = "ai_classification"
    METADATA_ANALYSIS = "metadata_analysis"
    STRUCTURAL_ANALYSIS = "structural_analysis"

class DocumentTypeIdentifierStep(StepBase):

    def __init__(self, id: str, name: str, enabled: bool, description: str = None, tags: List[str] = None, fail_step_on_document_error: bool = False, debug_mode: bool = False, services: List[str] = None, settings: dict = None, **kwargs):
        super().__init__(id=id, name=name, enabled=enabled, description=description, tags=tags, fail_step_on_document_error=fail_step_on_document_error, debug_mode=debug_mode, services=services, settings=settings, **kwargs)

        # Extract configuration settings
        self.identification_methods = [IdentificationMethod(m) for m in self.settings.get("identification_methods", 
                                                                                         ["magic_bytes", "file_extension"])]
        

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

        documents = input_data.data.get("documents", [])
        if not documents or not isinstance(documents, list):
            raise ValueError(f"No documents list found in input data.")

        _stats = {
            "total_documents": len(documents),
            "successful_documents": 0,
            "failed_documents": 0
        }

        # Iterate through each document in the input data
        logger.debug(f"Processing {len(documents)} documents...")

        final_documents_list = []

        for document in documents:
            try:

                if self.debug_mode:
                    logger.debug(f"Processing document: {document}")
                

                document_dict = document if isinstance(document, dict) else {"file_path": document}
                if not isinstance(document_dict, dict):
                    raise ValueError(f"Invalid document format: {document}. Expected a dictionary.")

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
        try:
            
            file_path = document.get("path", "")
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
            filepath = document.get("path", "")
            if not filepath:
                return {"error": "No filepath available", "confidence": 0.0, "method": "file_extension"}
            
            # Extract extension
            file_path = Path(filepath)
            extension = file_path.suffix.lower()
            
            # Map extensions to document types
            extension_mapping = {
                ".pdf": {"type": "pdf", "subtype": "portable_document", "category": "document"},
                ".docx": {"type": "word_document", "subtype": "openxml", "category": "office_document"},
                ".doc": {"type": "word_document", "subtype": "legacy", "category": "office_document"},
                ".xlsx": {"type": "excel_spreadsheet", "subtype": "openxml", "category": "spreadsheet"},
                ".xls": {"type": "excel_spreadsheet", "subtype": "legacy", "category": "spreadsheet"},
                ".pptx": {"type": "powerpoint_presentation", "subtype": "openxml", "category": "presentation"},
                ".ppt": {"type": "powerpoint_presentation", "subtype": "legacy", "category": "presentation"},
                ".txt": {"type": "text_document", "subtype": "plain_text", "category": "text"},
                ".rtf": {"type": "rich_text", "subtype": "rtf", "category": "text"},
                ".odt": {"type": "openoffice_document", "subtype": "text", "category": "office_document"},
                ".ods": {"type": "openoffice_spreadsheet", "subtype": "calc", "category": "spreadsheet"},
                ".odp": {"type": "openoffice_presentation", "subtype": "impress", "category": "presentation"},
                ".jpg": {"type": "image", "subtype": "jpeg", "category": "image"},
                ".jpeg": {"type": "image", "subtype": "jpeg", "category": "image"},
                ".png": {"type": "image", "subtype": "png", "category": "image"},
                ".gif": {"type": "image", "subtype": "gif", "category": "image"},
                ".bmp": {"type": "image", "subtype": "bitmap", "category": "image"},
                ".tiff": {"type": "image", "subtype": "tiff", "category": "image"},
                ".svg": {"type": "image", "subtype": "svg", "category": "image"},
                ".html": {"type": "web_document", "subtype": "html", "category": "web"},
                ".htm": {"type": "web_document", "subtype": "html", "category": "web"},
                ".xml": {"type": "structured_document", "subtype": "xml", "category": "text"},
                ".json": {"type": "data_document", "subtype": "json", "category": "text"},
                ".csv": {"type": "data_document", "subtype": "csv", "category": "text"},
                ".zip": {"type": "archive", "subtype": "zip", "category": "archive"},
                ".rar": {"type": "archive", "subtype": "rar", "category": "archive"},
                ".7z": {"type": "archive", "subtype": "7zip", "category": "archive"},
                ".tar": {"type": "archive", "subtype": "tar", "category": "archive"},
                ".gz": {"type": "archive", "subtype": "gzip", "category": "archive"}
            }
            
            if extension in extension_mapping:
                result = extension_mapping[extension]
                result.update({
                    "extension": extension,
                    "confidence": 0.7,
                    "method": "file_extension"
                })
                return result
            else:
                return {
                    "extension": extension,
                    "type": "unknown",
                    "confidence": 0.3,
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
            "file_extension": 0.8
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