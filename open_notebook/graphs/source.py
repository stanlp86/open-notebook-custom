import operator
import os
from typing import List
from pathlib import Path
from langchain_core.runnables import (
    RunnableConfig,
)
from open_notebook.config import UPLOADS_FOLDER
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from loguru import logger
from typing_extensions import Annotated, TypedDict

from open_notebook.domain.notebook import Asset, Source
from open_notebook.domain.transformation import Transformation
from open_notebook.graphs.content_processing import ContentState
from open_notebook.graphs.content_processing import graph as content_graph
from open_notebook.graphs.multipattern import graph as transform_graph
from open_notebook.utils import surreal_clean


class SourceState(TypedDict):
    content_state: ContentState
    transformations: List[str]
    notebook_id: str
    source: Source
    transformations: Annotated[list, operator.add]
    embed: bool


class TransformationState(TypedDict):
    source: Source
    transformation: dict


async def content_process(state: SourceState) -> dict:
    content_state = state["content_state"]
    logger.info("Content processing started for new content")
    processed_state = await content_graph.ainvoke(content_state)
    return {"content_state": processed_state}


async def run_patterns(input_text: str, patterns: List[dict]) -> str:
    output = await transform_graph.ainvoke(
        dict(content_stack=[input_text], patterns=patterns)
    )
    return output["output"]


# Add new function for bulk processing
async def process_bulk_sources(notebook_id, files, transformations, embed=False):
    """Process multiple source files in sequence with progress tracking"""
    results = []

    for idx, file in enumerate(files):
        logger.info(f"Processing file {idx+1}/{len(files)}: {file.name}")

        # Generate unique filename
        file_name = file.name
        file_extension = Path(file_name).suffix
        base_name = Path(file_name).stem

        # Create unique path
        new_path = os.path.join(UPLOADS_FOLDER, file_name)
        counter = 0
        while os.path.exists(new_path):
            counter += 1
            new_file_name = f"{base_name}_{counter}{file_extension}"
            new_path = os.path.join(UPLOADS_FOLDER, new_file_name)

        # Save the file
        with open(new_path, "wb") as f:
            f.write(file.getbuffer())

        # Process the file
        try:
            result = await source_graph.ainvoke(
                {
                    "content_state": {"file_path": new_path, "delete_source": True},
                    "notebook_id": notebook_id,
                    "transformations": transformations,
                    "embed": embed,
                }
            )
            results.append(
                {"success": True, "source": result.get("source"), "file": file_name}
            )
        except Exception as e:
            logger.error(f"Error processing file {file_name}: {str(e)}")
            results.append({"success": False, "error": str(e), "file": file_name})

    return results


def save_source(state: SourceState) -> dict:
    content_state = state["content_state"]

    source = Source(
        asset=Asset(
            url=content_state.get("url"), file_path=content_state.get("file_path")
        ),
        full_text=surreal_clean(content_state["content"]),
        title=content_state.get("title"),
    )
    source.save()

    if state["notebook_id"]:
        logger.debug(f"Adding source to notebook {state['notebook_id']}")
        source.add_to_notebook(state["notebook_id"])

    if state["embed"]:
        logger.debug("Embedding content for vector search")
        source.vectorize()

    return {"source": source}


def trigger_transformations(state: SourceState, config: RunnableConfig) -> List[Send]:
    if len(state["transformations"]) == 0:
        return []

    transformations = Transformation.get_all()
    to_apply = [
        t
        for t in transformations["source_insights"]
        if t["name"] in state["transformations"]
    ]
    logger.debug(f"Applying transformations {to_apply}")

    return [
        Send(
            "transform_content",
            {
                "source": state["source"],
                "transformation": t,
            },
        )
        for t in to_apply
    ]


async def transform_content(state: TransformationState) -> dict:
    source = state["source"]
    content = source.full_text
    if not content:
        return None
    transformation = state["transformation"]

    logger.debug(f"Applying transformation {transformation['name']}")
    result = await run_patterns(content, patterns=transformation["patterns"])

    source.add_insight(transformation["name"], surreal_clean(result))

    return {"transformations": [{"name": transformation["name"], "content": result}]}


# Create and compile the workflow
workflow = StateGraph(SourceState)

# Add nodes
workflow.add_node("content_process", content_process)
workflow.add_node("save_source", save_source)
workflow.add_node("transform_content", transform_content)
# Define the graph edges
workflow.add_edge(START, "content_process")
workflow.add_edge("content_process", "save_source")
workflow.add_conditional_edges(
    "save_source", trigger_transformations, ["transform_content"]
)
workflow.add_edge("transform_content", END)

# Compile the graph
source_graph = workflow.compile()
