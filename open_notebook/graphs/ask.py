import operator
from typing import Annotated, List, Optional

from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import (
    RunnableConfig,
)
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from open_notebook.domain.notebook import vector_search, Notebook
from open_notebook.graphs.utils import provision_langchain_model
from open_notebook.prompter import Prompter


class SubGraphState(TypedDict):
    question: str
    term: str
    # type: Literal["text", "vector"]
    instructions: str
    results: dict
    answer: str
    notebook_id: Optional[List[str]]  = None


class Search(BaseModel):
    term: str
    # type: Literal["text", "vector"] = Field(
    #     description="The type of search. Use 'text' for keyword search and 'vector' for semantic search. If you are using text, search always for a single word"
    # )
    instructions: str = Field(
        description="Tell the answeting LLM what information you need extracted from this search"
    )


class Strategy(BaseModel):
    reasoning: str
    searches: List[Search] = Field(
        default_factory=list,
        description="You can add up to five searches to this strategy",
    )


class ThreadState(TypedDict):
    question: str
    strategy: Strategy
    answers: Annotated[list, operator.add]
    final_answer: str
    notebook_id: Optional[List[str]]  = None


async def call_model_with_messages(state: ThreadState, config: RunnableConfig) -> dict:
    parser = PydanticOutputParser(pydantic_object=Strategy)
    system_prompt = Prompter(prompt_template="ask/entry", parser=parser).render(
        data=state
    )
    model = provision_langchain_model(
        system_prompt,
        config.get("configurable", {}).get("strategy_model"),
        "tools",
        max_tokens=6000,
    )
    # model = model.bind_tools(tools)
    ai_message = (model | parser).invoke(system_prompt)
    return {"strategy": ai_message}


async def trigger_queries(state: ThreadState, config: RunnableConfig):
    return [
        Send(
            "provide_answer",
            {
                "question": state["question"],
                "instructions": s.instructions,
                "term": s.term,
                "notebook_id": state.get("notebook_id"),
                # "type": s.type,
            },
        )
        for s in state["strategy"].searches
    ]

async def provide_answer(state: SubGraphState, config: RunnableConfig) -> dict:
    payload = state
    
    # Get notebook_id from state or config
    notebook_id = state.get("notebook_id")
    # if state["type"] == "text":
    #     results = text_search(state["term"], 10, True, True)
    # else:
    # Perform normal vector search
    results = vector_search(state["term"], 10, True, True)

    if notebook_id and isinstance(notebook_id, str):
        notebook_id = [notebook_id]
    # Filter by notebooks if IDs are provided
    if notebook_id and len(notebook_id) > 0:
        # Create a set to store all allowed IDs from multiple notebooks
        all_allowed_ids = set()
        
        # Gather allowed IDs from all selected notebooks
        for notebook_id_ in notebook_id:
            try:
                notebook = Notebook.get(notebook_id_)
                # Add source IDs and note IDs from this notebook
                source_ids = [source.id for source in notebook.sources]
                note_ids = [note.id for note in notebook.notes]
                all_allowed_ids.update(source_ids)
                all_allowed_ids.update(note_ids)
            except Exception as e:
                logger.error(f"Error getting notebook {notebook_id}: {str(e)}")
                continue
                
        # Filter results to only include items from this notebook
        results = [r for r in results if r.get("parent_id") in all_allowed_ids or r.get("id") in all_allowed_ids]
    
    if len(results) == 0:
        return {"answers": []}
        
    # Continue with existing code...
    payload["results"] = results
    ids = [r["id"] for r in results]
    payload["ids"] = ids
    system_prompt = Prompter(prompt_template="ask/query_process").render(data=payload)
    model = provision_langchain_model(
        system_prompt,
        config.get("configurable", {}).get("answer_model"),
        "tools",
        max_tokens=6000,
    )
    ai_message = model.invoke(system_prompt)
    return {"answers": [ai_message.content]}


async def write_final_answer(state: ThreadState, config: RunnableConfig) -> dict:
    system_prompt = Prompter(prompt_template="ask/final_answer").render(data=state)
    model = provision_langchain_model(
        system_prompt,
        config.get("configurable", {}).get("final_answer_model"),
        "tools",
        max_tokens= 6000,
    )
    ai_message = model.invoke(system_prompt)
    return {"final_answer": ai_message.content}


agent_state = StateGraph(ThreadState)
agent_state.add_node("agent", call_model_with_messages)
agent_state.add_node("provide_answer", provide_answer)
agent_state.add_node("write_final_answer", write_final_answer)
agent_state.add_edge(START, "agent")
agent_state.add_conditional_edges("agent", trigger_queries, ["provide_answer"])
agent_state.add_edge("provide_answer", "write_final_answer")
agent_state.add_edge("write_final_answer", END)

graph = agent_state.compile()
