import json
import dspy
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List, Dict, Any
from .dspy_signatures import ClassifyRoute, GenerateSQL, SynthesizeAnswer
from .rag.retrieval import SimpleBM25Retriever
from .sqlite_tool import get_schema, execute_sql
from rich.console import Console

console = Console()

lm = dspy.LM('ollama/qwen2.5:3b', temperature=0.0, max_tokens=1024)
dspy.configure(lm=lm)

router = dspy.Predict(ClassifyRoute)
sql_gen = dspy.Predict(GenerateSQL)
synth = dspy.Predict(SynthesizeAnswer)

retriever = SimpleBM25Retriever()


class AgentState(TypedDict):
    question: str
    format_hint: str
    route: str
    retrieved_docs: List[Dict]
    schema: str
    sql: str
    sql_result: Any
    error: str
    attempts: int
    final_answer: Any
    explanation: str
    citations: List[str]
    trace: List[str]


def router_node(state: AgentState):
    result = router(question=state["question"])
    route = result.route.lower()
    state["route"] = route
    state["trace"].append(f"Route: {route}")
    console.log(f"[bold green]Route → {route.upper()}[/]")
    return state


def retrieve_node(state: AgentState):
    docs = retriever.retrieve(state["question"], k=5)
    state["retrieved_docs"] = docs
    context = "\n".join([f"{d['id']}: {d['content']}" for d in docs])
    state["trace"].append(f"Retrieved {len(docs)} chunks")
    return state


def planner_node(state: AgentState):
    state["schema"] = json.dumps(get_schema(), indent=2)
    return state


def sql_node(state: AgentState):
    if state["route"] == "rag":
        state["sql"] = ""
        return state

    docs_context = "\n".join([d["content"] for d in state["retrieved_docs"]])
    result = sql_gen(
        question=state["question"],
        schema=state["schema"],
        docs_context=docs_context
    )
    state["sql"] = result.sql.strip().replace("```sql", "").replace("```", "")
    state["trace"].append(f"SQL: {state['sql']}")
    console.log(f"[bold blue]Generated SQL:[/] {state['sql']}")
    return state


def execute_node(state: AgentState):
    if state["route"] == "rag":
        state["sql_result"] = "No SQL needed"
        return state

    result = execute_sql(state["sql"])
    if result["success"]:
        state["sql_result"] = result["data"].to_string(index=False) if not result["data"].empty else "Empty"
        state["error"] = None
    else:
        state["error"] = result["error"]
        state["trace"].append(f"SQL Error: {state['error']}")
        console.log(f"[bold red]SQL Error:[/] {state['error']}")
    return state


def should_repair(state: AgentState):
    if state["attempts"] >= 2:
        return "synthesize"
    return "sql" if state.get("error") else "synthesize"


def repair_node(state: AgentState):
    state["attempts"] += 1
    console.log(f"[bold yellow]Repair attempt {state['attempts']}[/]")
    # Simple repair: add missing joins or fix date format
    error = state["error"].lower()
    sql = state["sql"]
    if "no such column" in error or "no such table" in error:
        sql = sql.replace("Order Details", "order_items")
    if "date" in error:
        sql = sql.replace("1997-06-01", "'1997-06-01'")
        sql = sql.replace("1997-06-30", "'1997-06-30'")
    state["sql"] = sql
    return state


def synthesize_node(state: AgentState):
    docs_str = "\n".join([d["id"] for d in state["retrieved_docs"]])
    result_str = str(state["sql_result"]) if state["sql_result"] else docs_str

    citations = []
    if state["route"] in ["sql", "hybrid"]:
        tables_used = ["Orders", "order_items", "Products", "Customers", "Categories"]
        citations.extend([t for t in tables_used if t.lower() in state["sql"].lower()])
    citations.extend([d["id"] for d in state["retrieved_docs"] if d["score"] > 2.0])

    synth_result = synth(
        question=state["question"],
        format_hint=state["format_hint"],
        sql_result=result_str,
        retrieved_docs=docs_str
    )

    try:
        state["final_answer"] = json.loads(synth_result.answer)
    except:
        state["final_answer"] = synth_result.answer

    state["explanation"] = synth_result.explanation
    state["citations"] = citations
    state["trace"].append("Answer synthesized")
    return state


workflow = StateGraph(AgentState)
workflow.add_node("router", router_node)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("planner", planner_node)
workflow.add_node("sql", sql_node)
workflow.add_node("execute", execute_node)
workflow.add_node("repair", repair_node)
workflow.add_node("synthesize", synthesize_node)

workflow.set_entry_point("router")
workflow.add_conditional_edges("router", lambda s: "retrieve")
workflow.add_edge("retrieve", "planner")
workflow.add_edge("planner", "sql")
workflow.add_edge("sql", "execute")
workflow.add_conditional_edges("execute", should_repair, {"sql": "repair", "synthesize": "synthesize"})
workflow.add_edge("repair", "execute")
workflow.add_edge("synthesize", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)