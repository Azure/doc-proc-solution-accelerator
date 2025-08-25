import json
import pandas as pd
import threading
import logging

from typing import List, Dict

from .docproc_state_service import DocProcStateService
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.docproc_state import DocProcState, DocProcStateItem
from doc.proc.models.docproc_artifact import DocProcArtifactType
from doc.proc.models.docproc_pipeline_state import DocProcPipelineState
from doc.proc.models.docproc_artifact import DocProcArtifact

from connectors.blob import AzureBlobClient

class BlobStorageDocProcStateService(DocProcStateService):

    BLOB_STORAGE_CONTAINER_NAME = "docproc-state"
    EXECUTION_STATE_DIRECTORY = "execution-state"
    PIPELINE_STATE_DIRECTORY = "pipeline-state"

    storageService : AzureBlobClient = None
    semaphore = threading.Semaphore(1)

    def __init__(self, storageService: AzureBlobClient):
        self.storageService = storageService

    def get_source_items(self, source):
        files = self.storageService.get_files(self.BLOB_STORAGE_CONTAINER_NAME, f"{self.EXECUTION_STATE_DIRECTORY}/{source['catalog_id']}")  

        for file in files:
            content = self.storageService.download_blob(self.BLOB_STORAGE_CONTAINER_NAME, file.name)
            yield content.decode()

    async def has_state(self, request: DocProcRequest) -> bool:
        return await self.storageService.file_exists_async(
            self.BLOB_STORAGE_CONTAINER_NAME,
            f"{self.EXECUTION_STATE_DIRECTORY}/{self.get_persistence_identifier(request)}.json")    

    async def get_state(self, request :DocProcRequest) -> DocProcState:

        content = await self.storageService.read_file_async(
            self.BLOB_STORAGE_CONTAINER_NAME,
            f"{self.EXECUTION_STATE_DIRECTORY}/{self.get_persistence_identifier(request)}.json")

        content = json.loads(content.decode())

        if type(content) is dict:
            return DocProcState(**content)
        else:
            return DocProcState(**json.loads(content))

    async def load_artifacts(self, state:DocProcState, artifactType:DocProcArtifactType):

        if (artifactType in state.loaded_artifact_types):
            return

        persistenceIdentifier = self.get_persistence_identifier(state)

        match (artifactType):
            case DocProcArtifactType.ExtractedText:

                for artifact in state.artifacts:
                    if artifact.type == DocProcArtifactType.ExtractedText:
                        extractedTextArtifact : DocProcArtifact = artifact

                if (extractedTextArtifact != None):
                    extractedTextArtifact.content = await self.storageService.read_file_async(
                        self.BLOB_STORAGE_CONTAINER_NAME,
                            f"{self.EXECUTION_STATE_DIRECTORY}/{extractedTextArtifact.canonical_id}.txt")

                state.loaded_artifact_types.append(DocProcArtifactType.ExtractedText)

            case DocProcArtifactType.TextPartition:
                pass
            case DocProcArtifactType.TextEmbeddingVector:

                await self.align_items(state, persistenceIdentifier)

                state.loaded_artifact_types.append(
                    [
                        DocProcArtifactType.TextPartition,
                        DocProcArtifactType.TextEmbeddingVector
                    ])

            case _:
                raise Exception(f"The artifact type {artifactType} is not supported.")

    async def save_state(self, state : DocProcState):
        persistenceIdentifier = self.get_persistence_identifier(state)

        for artifact in state.artifacts:
            if artifact.type == DocProcArtifactType.ExtractedText:
                
                if (artifact.is_dirty):

                    artifact.canonical_id = f"{persistenceIdentifier}_{artifact.type.lower()}"

                    await self.storageService.write_file_async(self.BLOB_STORAGE_CONTAINER_NAME,
                        f"{self.EXECUTION_STATE_DIRECTORY}/{artifact.canonical_id}.txt",
                        artifact.content)

            if (artifact.type == DocProcArtifactType.TextPartition 
                or artifact.type == DocProcArtifactType.TextEmbeddingVector):

                if artifact.is_dirty:
                    artifact.content_hash = self.hash_text(artifact.content)
                    artifact.canonical_id = f"{persistenceIdentifier}_{artifact.type.lower()}_{artifact.position}"

        await self.save_text_partitions_and_embeddings(state, persistenceIdentifier)

        content = state.model_dump_json()

        await self.storageService.write_file_async(
            self.BLOB_STORAGE_CONTAINER_NAME,
            f"{self.EXECUTION_STATE_DIRECTORY}/{persistenceIdentifier}.json",
            content)
        

    async def save_text_partitions_and_embeddings(self, state : DocProcState, persistenceIdentifier : str):
        
        needs_aligned = False

        for artifact in state.artifacts:
            if artifact.is_dirty and (artifact.type == DocProcArtifactType.TextPartition or artifact.type == DocProcArtifactType.TextEmbeddingVector):
                needs_aligned = True
                break

        if not needs_aligned:
            return

        await self.align_items(state, persistenceIdentifier)

        textPartitions = []

        for artifact in state.artifacts:
            if (artifact.type == DocProcArtifactType.TextPartition
                and not artifact.content):
                textPartitions.append(artifact)

        textPartitions.sort(key=lambda a: a.position)

        if (len(textPartitions) == 0):
            return

        items = []

        for tp in textPartitions:
            for te in state.artifacts:
                if (te.type == DocProcArtifactType.TextEmbeddingVector
                    and te.position == tp.position):
                    items.append(DocProcStateItem(**{
                            'PipelineName': "NoPipeline" if state.pipeline_name is None else state.pipeline_name,
                            'Position': tp.position,
                            'TextPartitionContent': tp.content,
                            'TextPartitionHash': tp.content_hash,
                            'TextPartitionSize': tp.size,
                            'TextEmbeddingVectorSize': 0 if te is None else te.size
                        }
                    ))

            vsi = DocProcStateItem(**{
                    'PipelineName': "NoPipeline" if state.pipeline_name is None else state.pipeline_name,
                    'Position': tp.position,
                    'TextPartitionContent': tp.content,
                    'TextPartitionHash': tp.content_hash,
                    'TextPartitionSize': tp.size,
                    'TextEmbeddingVectorSize': 0 if te is None else te.size,
                    'TextEmbeddingVector': None if (te is None or not te.content) else json.loads(te.content).vector,
                    'TextEmbeddingVectorHash': None if te is None else te.content_hash
                }
            )

        await self.save_items(items, persistenceIdentifier)

    async def save_items(self, items : List[DocProcStateItem], persistenceIdentifier : str):
        df = pd.DataFrame(items)

        serializedParquet = df.to_parquet(index=False, compression='snappy')

        await self.storageService.write_file_async(
            self.BLOB_STORAGE_CONTAINER_NAME,
            f"{self.EXECUTION_STATE_DIRECTORY}/{persistenceIdentifier}.snappy.parquet",
            serializedParquet,
            "application/vnd.apache.parquet")

    async def load_items(self, persistenceIdentifier : str):
        filePath = f"{self.EXECUTION_STATE_DIRECTORY}/{persistenceIdentifier}.snappy.parquet"

        if not await self.storageService.file_exists_async(
            self.BLOB_STORAGE_CONTAINER_NAME,
            filePath):
            return []

        binaryContent = await self.storageService.read_file_async(
            self.BLOB_STORAGE_CONTAINER_NAME,
            filePath)
        
        return pd.read_parquet(binaryContent, engine='pyarrow')
            
    async def align_items(self, state : DocProcState, persistenceIdentifier : str):
        items = await self.load_items(persistenceIdentifier)

        for textPartitionArtifact in state.artifacts:
            if textPartitionArtifact.type == DocProcArtifactType.TextPartition and not textPartitionArtifact.is_dirty:
                if items[textPartitionArtifact.position] != None:
                    item = items[textPartitionArtifact.position]
                    textPartitionArtifact.content = item.text_partition_content
                    textPartitionArtifact.content_hash = item.text_partition_hash
                    textPartitionArtifact.size = item.text_partition_size
            
        for textEmbeddingArtifact in state.artifacts:
            if textEmbeddingArtifact.type == DocProcArtifactType.TextEmbeddingVector and not textEmbeddingArtifact.is_dirty:
                if items[textEmbeddingArtifact.position] != None:
                    item = items[textEmbeddingArtifact.position]
                    textEmbeddingArtifact.content = None if item.text_embedding_vector == None else json.dumps(item.text_embedding_vector)
                    textEmbeddingArtifact.content_hash = item.text_embedding_vector_hash
                    textEmbeddingArtifact.size = item.text_embedding_vector_size

    async def save_pipeline_state(self, state : DocProcPipelineState):
        pipelineName = state.pipeline_object_id.split('/').last()
        pipelineStatePath = f"{self.PIPELINE_STATE_DIRECTORY}/{pipelineName}/{pipelineName}-{state.execution_id}.json"
        content = json.dumps(state)

        with self.semaphore:
            try:
                await self.storageService.write_file_async(
                    self.BLOB_STORAGE_CONTAINER_NAME,
                    pipelineStatePath,
                    content)
            except Exception as ex:
                logging.error(f"Error saving pipeline state: {ex}")

    async def read_pipeline_state(self, pipelineName: str, pipelineExecutionId: str):
        pipelineStatePath = f"{self.PIPELINE_STATE_DIRECTORY}/{pipelineName}/{pipelineName}-{pipelineExecutionId}.json"
        content = await self.storageService.read_file_async(
            self.BLOB_STORAGE_CONTAINER_NAME,
            pipelineStatePath)

        return json.loads(content)