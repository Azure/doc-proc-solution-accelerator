import os
from uuid import uuid4
import logging
import networkx as nx
import pandas as pd
import numpy as np
import yaml
import json

from typing import List, Dict, Set, cast, Any
from pathlib import Path
from datetime import datetime, timezone
from string import Template

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.content_identifier import ContentIdentifier
from doc.proc.models.docproc_state import DocProcState

from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.config.enums import CacheType, IndexingMethod
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.utils.api import create_cache_from_config, create_storage_from_config
from graphrag.config.defaults import graphrag_config_defaults
from graphrag.index.operations.extract_graph.graph_extractor import GraphExtractor
from graphrag.language_model.manager import ModelManager
from graphrag.index.operations.extract_graph.typing import (
    Document,
    EntityExtractStrategy,
    ExtractEntityStrategyType,
    EntityExtractionResult,
    EntityTypes,
    StrategyConfig,
)

from graphrag.prompts.index.extract_graph import (
    CONTINUE_PROMPT,
    GRAPH_EXTRACTION_PROMPT,
    LOOP_PROMPT,
)

from pydantic import BaseModel, Field

from doc.proc.models.schemas import (
    COMMUNITY_REPORTS_FINAL_COLUMNS,
    COMMUNITIES_FINAL_COLUMNS
)

logger = logging.getLogger("doc.proc.step.graph_rag") # need to specify the logger name as this module is loaded dynamically

log = logging.getLogger(__name__)

from dependencies import get_config
config = get_config()

from connectors.cosmosdb import CosmosDBClient
cosmos = CosmosDBClient(config)

DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event", "organism", "protein", "gene", "chemical", "disease", "anatomy"]

from graphrag.config.defaults import graphrag_config_defaults


class EmbedGraphConfig(BaseModel):
    """The default configuration section for Node2Vec."""

    enabled: bool = Field(
        description="A flag indicating whether to enable node2vec.",
        default=graphrag_config_defaults.embed_graph.enabled,
    )
    dimensions: int = Field(
        description="The node2vec vector dimensions.",
        default=graphrag_config_defaults.embed_graph.dimensions,
    )
    num_walks: int = Field(
        description="The node2vec number of walks.",
        default=graphrag_config_defaults.embed_graph.num_walks,
    )
    walk_length: int = Field(
        description="The node2vec walk length.",
        default=graphrag_config_defaults.embed_graph.walk_length,
    )
    window_size: int = Field(
        description="The node2vec window size.",
        default=graphrag_config_defaults.embed_graph.window_size,
    )
    iterations: int = Field(
        description="The node2vec iterations.",
        default=graphrag_config_defaults.embed_graph.iterations,
    )
    random_seed: int = Field(
        description="The node2vec random seed.",
        default=graphrag_config_defaults.embed_graph.random_seed,
    )
    use_lcc: bool = Field(
        description="Whether to use the largest connected component.",
        default=graphrag_config_defaults.embed_graph.use_lcc,
    )

class GraphRagStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        self.root_dir: Path = Path(self.settings.get("root_dir", "."))
        self.config_filepath: Path = Path(self.settings.get("config_filepath", "gr_config.yaml"))
        self.cli_overrides: Dict = self.settings.get("cli_overrides", {})
        self.output_dir: Path | None = self.settings.get("output_dir", None)

        self.method: IndexingMethod = IndexingMethod(self.settings.get("method", "standard"))
        self.verbose: bool = self.settings.get("verbose", False)
        self.memprofile: bool = self.settings.get("memprofile", False)
        self.cache: bool = self.settings.get("cache", False)
        self.dry_run: bool = self.settings.get("dry_run", False)
        self.skip_validation: bool = self.settings.get("skip_validation", False)
        self.is_update_run: bool = self.settings.get("is_update_run", False)
        self.verbose: bool = self.settings.get("verbose", False)

        if self.output_dir:
            self.cli_overrides["output.base_dir"] = str(self.output_dir)
            self.cli_overrides["reporting.base_dir"] = str(self.output_dir)
            self.cli_overrides["update_index_output.base_dir"] = str(self.output_dir)

        self.graphrag_config : GraphRagConfig = self.load_config(self.cli_overrides)

        self.input_storage = create_storage_from_config(self.graphrag_config.input.storage)
        self.output_storage = create_storage_from_config(self.graphrag_config.output)
        self.cache = create_cache_from_config(self.graphrag_config.cache, self.root_dir)

        self.entity_types: List[str] = self.settings.get("entity_types", DEFAULT_ENTITY_TYPES)

        self.tuple_delimiter = self.settings.get("tuple_delimiter", None)
        self.record_delimiter = self.settings.get("record_delimiter", None)
        self.completion_delimiter = self.settings.get("completion_delimiter", None)
        self.extraction_prompt = self.settings.get("extraction_prompt", None)

        graph_prompt = self.cosmos.get_document('prompts','graphrag_extration')
        self.extraction_prompt = graph_prompt['system_prompt'] if graph_prompt else self.extraction_prompt

        CONTINUE_PROMPT = self.cosmos.get_document('prompts','graphrag_continue')['system_prompt']
        LOOP_PROMPT = self.cosmos.get_document('prompts','graphrag_loop')['system_prompt']
        GRAPH_EXTRACTION_PROMPT = self.extraction_prompt

        self.max_gleanings = self.settings.get(
            "max_gleanings", graphrag_config_defaults.extract_graph.max_gleanings
        )

        self.model = self._get_model()

        self.openai_url = self.model.get("endpoint", None)
        self.openai_key = self.config.get("AI_FOUNDRY_ACCOUNT_APIKEY", None)
        self.openai_deployment = self.model.get("name", None)
        self.openai_model = self.model.get("model", None)
        self.openai_api_version = self.model.get("apiVersion", "2024-05-01-preview")

        self.embedding_model = self._get_model("EMBEDDING_DEPLOYMENT_NAME")

        data = {'api_key': self.openai_key, 
                'auth_type': 'api_key', 
                'type': 'azure_openai_chat', 
                'model': self.openai_model, 
                'encoding_model': 'o200k_base',
                'api_base': self.openai_url,
                'api_version': self.openai_api_version, 
                'deployment_name': self.openai_deployment, 
                'organization': None, 'proxy': None, 'audience': None, 
                'model_supports_json': True, 'request_timeout': 180.0, 
                'tokens_per_minute': 'auto', 'requests_per_minute': 'auto', 
                'retry_strategy': 'native', 'max_retries': 10, 'max_retry_wait': 10.0, 
                'concurrent_requests': 25, 'async_mode': 'threaded', 
                'responses': None, 'max_tokens': None, 'temperature': 0, 'max_completion_tokens': None, 
                'reasoning_effort': None, 'top_p': 1, 'n': 1, 'frequency_penalty': 0.0, 
                'presence_penalty': 0.0
        }

        llm_config = LanguageModelConfig(**data)
        cache = None
        callbacks: WorkflowCallbacks = None

        self.llm = ModelManager().get_or_create_chat_model(
            name="extract_graph",
            model_type=llm_config.type,
            config=llm_config,
            callbacks=callbacks,
            cache=cache,
        )

        self.extractor = GraphExtractor(
            model_invoker=self.llm,
            prompt=self.extraction_prompt,
            max_gleanings=self.max_gleanings,
            on_error=lambda e, s, d: (
                callbacks.error("Entity Extraction Error", e, s, d) if callbacks else None
            ),
        )

    def load_config(self, cli_overrides: dict) -> GraphRagConfig:
        config_text = self.cosmos.get_document('docproc','gr_config').get('system_prompt', '')
        config_text = self._parse_env_variables(config_text)
        config_data = self._parse('yaml', config_text)
        if cli_overrides:
            self._apply_overrides(config_data, cli_overrides)
        return GraphRagConfig(**config_data)
    
    def _apply_overrides(self, data: dict[str, Any], overrides: dict[str, Any]) -> None:
        """Apply the overrides to the raw configuration."""
        for key, value in overrides.items():
            keys = key.split(".")
            target = data
            current_path = keys[0]
            for k in keys[:-1]:
                current_path += f".{k}"
                target_obj = target.get(k, {})
                if not isinstance(target_obj, dict):
                    msg = f"Cannot override non-dict value: data[{current_path}] is not a dict."
                    raise TypeError(msg)
                target[k] = target_obj
                target = target[k]
            target[keys[-1]] = value


    def _parse(self, file_extension: str, contents: str) -> dict[str, Any]:
        """Parse configuration."""
        match file_extension:
            case ".yaml" | ".yml" | "yaml" | "yml":
                return yaml.safe_load(contents)
            case ".json" | "json":
                return json.loads(contents)
            case _:
                msg = (
                    f"Unable to parse config. Unsupported file extension: {file_extension}"
                )
                raise ValueError(msg)
    
    def _parse_env_variables(self,text: str) -> str:
        """Parse environment variables in the configuration text.

        Parameters
        ----------
        text : str
            The configuration text.

        Returns
        -------
        str
            The configuration text with environment variables parsed.

        Raises
        ------
        KeyError
            If an environment variable is not found.
        """
        try:
            text = Template(text).substitute(config.config)
        except KeyError:
            try:
                text = Template(text).substitute(os.environ)
            except KeyError as e:
                msg = f"Environment variable not found: {e}"
                print(msg)

        return text
    
    async def get_document(self, content_identifier: ContentIdentifier, context: "PipelineExecutionContext") -> dict:
        """
        Retrieve a document by its content identifier.
        """
        document = await context.pipeline.get_document(content_identifier)
        return document
    
    async def process_document(self, document, context: "PipelineExecutionContext", request: DocProcRequest, state: DocProcState):

        try:
            content = self._get_content(document)
            #content_metadata = await self._get_content_metadata(document)
            #content_metadata_security = await self._get_content_security(document)

            print('Running GraphRAG indexing...')
            doc = Document(text=content, id=str(document['id']))
            docs = [doc]
            
            text_list = [doc.text.strip() for doc in docs]

            results = await self.extractor(
                list(text_list),
                {
                    "entity_types": self.entity_types,
                    "tuple_delimiter": self.tuple_delimiter,
                    "record_delimiter": self.record_delimiter,
                    "completion_delimiter": self.completion_delimiter,
                },
            )

            graph = results.output
            # Map the "source_id" back to the "id" field
            for _, node in graph.nodes(data=True):  # type: ignore
                if node is not None:
                    node["source_id"] = ",".join(
                        docs[int(id)].id for id in node["source_id"].split(",")
                    )

            for _, _, edge in graph.edges(data=True):  # type: ignore
                if edge is not None:
                    edge["source_id"] = ",".join(
                        docs[int(id)].id for id in edge["source_id"].split(",")
                    )

            entities = [
                ({"title": item[0], **(item[1] or {})})
                for item in graph.nodes(data=True)
                if item is not None
            ]

            relationships = nx.to_pandas_edgelist(graph)

            graph_dict = nx.node_link_data(graph, edges="edges")

            ee_result = EntityExtractionResult(entities, relationships, graph)
            metadata = document.get("metadata", {})
            existing_entities= metadata.get("entity_ids", [])
            metadata["entity_ids"] = entities + existing_entities if existing_entities else entities
            existing_relationships= metadata.get("relationship_ids", [])
            metadata["relationship_ids"] = relationships.to_dict(orient="records") + existing_relationships if existing_relationships else relationships.to_dict(orient="records")
            metadata["graph"] = graph_dict
            return ee_result

        except Exception as e:
            message = f"Error processing document {document['id']}: {e}"
            logger.error(message)
            raise StepExecutionError(message)

    def _load_strategy(strategy_type: ExtractEntityStrategyType) -> EntityExtractStrategy:
        """Load strategy method definition."""
        match strategy_type:
            case ExtractEntityStrategyType.graph_intelligence:
                from graphrag.index.operations.extract_graph.graph_intelligence_strategy import (
                    run_graph_intelligence,
                )

                return run_graph_intelligence

            case _:
                msg = f"Unknown strategy: {strategy_type}"
                raise ValueError(msg)
    
    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", request: DocProcRequest, state: DocProcState) -> Dict:
        """
        Process a single document to extract content.
        
        :param document: Document dictionary containing file path and other metadata.
        :param context: PipelineExecutionContext instance.
        :param ai_model_inference_service: AI Model Inference Service instance.
        :return: Dictionary with processing statistics.
        """

        document = input_data.data.get('documents', [])[0]
        if not document:
            document = await self.get_document(request.content_identifier, context)

        state.content_identifier.metadata = document
        await self.process_document(document, context, request, state)
        input_data.data['documents'] = [document]

        return input_data
    
    def create_graph(
            self,
        edges: pd.DataFrame,
        edge_attr: list[str | int] | None = None,
        nodes: pd.DataFrame | None = None,
        node_id: str = "title",
    ) -> nx.Graph:
        """Create a networkx graph from nodes and edges dataframes."""
        graph = nx.from_pandas_edgelist(edges, edge_attr=edge_attr)

        if nodes is not None:
            nodes.set_index(node_id, inplace=True)
            graph.add_nodes_from((n, dict(d)) for n, d in nodes.iterrows())

        return graph
    
    def create_communities(
            self,
        entities: pd.DataFrame,
        relationships: pd.DataFrame,
        max_cluster_size: int,
        use_lcc: bool,
        seed: int | None = None,
    ) -> pd.DataFrame:
        """All the steps to transform final communities."""
        graph = self.create_graph(relationships, edge_attr=["weight"])

        clusters = self.cluster_graph(
            graph,
            max_cluster_size,
            use_lcc,
            seed=seed,
        )

        communities = pd.DataFrame(
            clusters, columns=pd.Index(["level", "community", "parent", "title"])
        ).explode("title")
        communities["community"] = communities["community"].astype(int)

        # aggregate entity ids for each community
        entity_ids = communities.merge(entities, on="title", how="inner")
        entity_ids = (
            entity_ids.groupby("community").agg(entity_ids=("id", list)).reset_index()
        )

        # aggregate relationships ids for each community
        # these are limited to only those where the source and target are in the same community
        max_level = communities["level"].max()
        all_grouped = pd.DataFrame(
            columns=["community", "level", "relationship_ids", "text_unit_ids"]  # type: ignore
        )
        for level in range(max_level + 1):
            communities_at_level = communities.loc[communities["level"] == level]
            sources = relationships.merge(
                communities_at_level, left_on="source", right_on="title", how="inner"
            )
            targets = sources.merge(
                communities_at_level, left_on="target", right_on="title", how="inner"
            )
            matched = targets.loc[targets["community_x"] == targets["community_y"]]
            text_units = matched.explode("text_unit_ids")
            grouped = (
                text_units.groupby(["community_x", "level_x", "parent_x"])
                .agg(relationship_ids=("id", list), text_unit_ids=("text_unit_ids", list))
                .reset_index()
            )
            grouped.rename(
                columns={
                    "community_x": "community",
                    "level_x": "level",
                    "parent_x": "parent",
                },
                inplace=True,
            )
            all_grouped = pd.concat([
                all_grouped,
                grouped.loc[
                    :, ["community", "level", "parent", "relationship_ids", "text_unit_ids"]
                ],
            ])

        # deduplicate the lists
        all_grouped["relationship_ids"] = all_grouped["relationship_ids"].apply(
            lambda x: sorted(set(x))
        )
        all_grouped["text_unit_ids"] = all_grouped["text_unit_ids"].apply(
            lambda x: sorted(set(x))
        )

        # join it all up and add some new fields
        final_communities = all_grouped.merge(entity_ids, on="community", how="inner")
        final_communities["id"] = [str(uuid4()) for _ in range(len(final_communities))]
        final_communities["human_readable_id"] = final_communities["community"]
        final_communities["title"] = "Community " + final_communities["community"].astype(
            str
        )
        final_communities["parent"] = final_communities["parent"].astype(int)
        # collect the children so we have a tree going both ways
        parent_grouped = cast(
            "pd.DataFrame",
            final_communities.groupby("parent").agg(children=("community", "unique")),
        )
        final_communities = final_communities.merge(
            parent_grouped,
            left_on="community",
            right_on="parent",
            how="left",
        )
        # replace NaN children with empty list
        final_communities["children"] = final_communities["children"].apply(
            lambda x: x if isinstance(x, np.ndarray) else []  # type: ignore
        )
        # add fields for incremental update tracking
        final_communities["period"] = datetime.now(timezone.utc).date().isoformat()
        final_communities["size"] = final_communities.loc[:, "entity_ids"].apply(len)

        return final_communities.loc[
            :,
            COMMUNITIES_FINAL_COLUMNS,
        ]
    
    def finalize_community_reports(
            self,
        reports: pd.DataFrame,
        communities: pd.DataFrame,
    ) -> pd.DataFrame:
        """All the steps to transform final community reports."""
        # Merge with communities to add shared fields
        community_reports = reports.merge(
            communities.loc[:, ["community", "parent", "children", "size", "period"]],
            on="community",
            how="left",
            copy=False,
        )

        community_reports["community"] = community_reports["community"].astype(int)
        community_reports["human_readable_id"] = community_reports["community"]
        community_reports["id"] = [uuid4().hex for _ in range(len(community_reports))]

        return community_reports.loc[
            :,
            COMMUNITY_REPORTS_FINAL_COLUMNS,
        ]
    
    def finalize_entities(
            self,
        entities: pd.DataFrame,
        relationships: pd.DataFrame,
        callbacks: WorkflowCallbacks,
        embed_config: EmbedGraphConfig | None = None,
        layout_enabled: bool = False,
    ) -> pd.DataFrame:
        """All the steps to transform final entities."""
        graph = self.create_graph(relationships, edge_attr=["weight"])
        graph_embeddings = None
        if embed_config is not None and embed_config.enabled:
            graph_embeddings = self.embed_graph(
                graph,
                embed_config,
            )
        layout = self.layout_graph(
            graph,
            callbacks,
            layout_enabled,
            embeddings=graph_embeddings,
        )
        degrees = self.compute_degree(graph)
        final_entities = (
            entities.merge(layout, left_on="title", right_on="label", how="left")
            .merge(degrees, on="title", how="left")
            .drop_duplicates(subset="title")
        )
        final_entities = final_entities.loc[entities["title"].notna()].reset_index()
        # disconnected nodes and those with no community even at level 0 can be missing degree
        final_entities["degree"] = final_entities["degree"].fillna(0).astype(int)
        final_entities.reset_index(inplace=True)
        final_entities["human_readable_id"] = final_entities.index
        final_entities["id"] = final_entities["human_readable_id"].apply(
            lambda _x: str(uuid4())
        )
        return final_entities.loc[
            :,
            ENTITIES_FINAL_COLUMNS,
        ]

    def graph_to_dataframes(
            self,
        graph: nx.Graph,
        node_columns: list[str] | None = None,
        edge_columns: list[str] | None = None,
        node_id: str = "title",
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Deconstructs an nx.Graph into nodes and edges dataframes."""
        # nx graph nodes are a tuple, and creating a df from them results in the id being the index
        nodes = pd.DataFrame.from_dict(dict(graph.nodes(data=True)), orient="index")
        nodes[node_id] = nodes.index
        nodes.reset_index(inplace=True, drop=True)

        edges = nx.to_pandas_edgelist(graph)

        # we don't deal in directed graphs, but we do need to ensure consistent ordering for df joins
        # nx loses the initial ordering
        edges["min_source"] = edges[["source", "target"]].min(axis=1)
        edges["max_target"] = edges[["source", "target"]].max(axis=1)
        edges = edges.drop(columns=["source", "target"]).rename(
            columns={"min_source": "source", "max_target": "target"}  # type: ignore
        )

        if node_columns:
            nodes = nodes.loc[:, node_columns]

        if edge_columns:
            edges = edges.loc[:, edge_columns]

        return (nodes, edges)

    def prune_graph(
            self,
        graph: nx.Graph,
        min_node_freq: int = 1,
        max_node_freq_std: float | None = None,
        min_node_degree: int = 1,
        max_node_degree_std: float | None = None,
        min_edge_weight_pct: float = 40,
        remove_ego_nodes: bool = False,
        lcc_only: bool = False,
    ) -> nx.Graph:
        """Prune graph by removing nodes that are out of frequency/degree ranges and edges with low weights."""
        # remove ego nodes if needed
        degree = cast("DegreeView", graph.degree)
        degrees = list(degree())  # type: ignore
        if remove_ego_nodes:
            # ego node is one with highest degree
            ego_node = max(degrees, key=lambda x: x[1])
            graph.remove_nodes_from([ego_node[0]])

        # remove nodes that are not within the predefined degree range
        graph.remove_nodes_from([
            node for node, degree in degrees if degree < min_node_degree
        ])
        if max_node_degree_std is not None:
            upper_threshold = self._get_upper_threshold_by_std(
                [degree for _, degree in degrees], max_node_degree_std
            )
            graph.remove_nodes_from([
                node for node, degree in degrees if degree > upper_threshold
            ])

        # remove nodes that are not within the predefined frequency range
        graph.remove_nodes_from([
            node
            for node, data in graph.nodes(data=True)
            if data[schemas.NODE_FREQUENCY] < min_node_freq
        ])
        if max_node_freq_std is not None:
            upper_threshold = self._get_upper_threshold_by_std(
                [data[schemas.NODE_FREQUENCY] for _, data in graph.nodes(data=True)],
                max_node_freq_std,
            )
            graph.remove_nodes_from([
                node
                for node, data in graph.nodes(data=True)
                if data[schemas.NODE_FREQUENCY] > upper_threshold
            ])

        # remove edges by min weight
        if min_edge_weight_pct > 0:
            min_edge_weight = np.percentile(
                [data[schemas.EDGE_WEIGHT] for _, _, data in graph.edges(data=True)],
                min_edge_weight_pct,
            )
            graph.remove_edges_from([
                (source, target)
                for source, target, data in graph.edges(data=True)
                if source in graph.nodes()
                and target in graph.nodes()
                and data[schemas.EDGE_WEIGHT] < min_edge_weight
            ])

        if lcc_only:
            return glc.utils.largest_connected_component(graph)  # type: ignore

        return graph


    def _get_upper_threshold_by_std(
            self,
        data: list[float] | list[int], std_trim: float
    ) -> float:
        """Get upper threshold by standard deviation."""
        mean = np.mean(data)
        std = np.std(data)
        return mean + std_trim * std  # type: ignore


    def _merge_entities(entity_dfs) -> pd.DataFrame:
        all_entities = pd.concat(entity_dfs, ignore_index=True)
        return (
            all_entities.groupby(["title", "type"], sort=False)
            .agg(
                description=("description", list),
                text_unit_ids=("source_id", list),
                frequency=("source_id", "count"),
            )
            .reset_index()
        )
    
    def compute_edge_combined_degree(
            self,
        edge_df: pd.DataFrame,
        node_degree_df: pd.DataFrame,
        node_name_column: str,
        node_degree_column: str,
        edge_source_column: str,
        edge_target_column: str,
    ) -> pd.Series:
        """Compute the combined degree for each edge in a graph."""

        def join_to_degree(df: pd.DataFrame, column: str) -> pd.DataFrame:
            degree_column = self._degree_colname(column)
            result = df.merge(
                node_degree_df.rename(
                    columns={node_name_column: column, node_degree_column: degree_column}
                ),
                on=column,
                how="left",
            )
            result[degree_column] = result[degree_column].fillna(0)
            return result

        output_df = join_to_degree(edge_df, edge_source_column)
        output_df = join_to_degree(output_df, edge_target_column)
        output_df["combined_degree"] = (
            output_df[self._degree_colname(edge_source_column)]
            + output_df[self._degree_colname(edge_target_column)]
        )
        return cast("pd.Series", output_df["combined_degree"])


    def _degree_colname(self, column: str) -> str:
        return f"{column}_degree"


    def compute_degree(self, graph: nx.Graph) -> pd.DataFrame:
        """Create a new DataFrame with the degree of each node in the graph."""
        return pd.DataFrame([
            {"title": node, "degree": int(degree)}
            for node, degree in graph.degree  # type: ignore
        ])


    def _merge_relationships(self, relationship_dfs) -> pd.DataFrame:
        all_relationships = pd.concat(relationship_dfs, ignore_index=False)
        return (
            all_relationships.groupby(["source", "target"], sort=False)
            .agg(
                description=("description", list),
                text_unit_ids=("source_id", list),
                weight=("weight", "sum"),
            )
            .reset_index()
        )