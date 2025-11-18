
import json
import click
from agent.graph_hybrid import app, AgentState
from rich.console import Console

console = Console()


@click.command()
@click.option("--batch", required=True, help="Path to jsonl eval file")
@click.option("--out", default="outputs_hybrid.jsonl", help="Output file")
def run(batch: str, out: str):
    outputs = []
    with open(batch) as f:
        questions = [json.loads(line) for line in f]

    for q in questions:
        console.log(f"\n[bold cyan]Question {q['id']}:[/] {q['question']}")

        inputs = {
            "question": q["question"],
            "format_hint": q["format_hint"],
            "attempts": 0,
            "trace": [],
            "citations": [],
            "retrieved_docs": []
        }

        result = app.invoke(inputs, config={"configurable": {"thread_id": q["id"]}})

        confidence = 1.0 if result.get("error") is None and result["attempts"] == 0 else 0.8 if result[
                                                                                                    "attempts"] == 1 else 0.6

        output = {
            "id": q["id"],
            "final_answer": result["final_answer"],
            "sql": result["sql"] if result["sql"] else "",
            "confidence": round(confidence, 2),
            "explanation": result["explanation"],
            "citations": result["citations"]
        }
        outputs.append(output)
        console.log(f"[bold green]✓ Answer: {result['final_answer']}[/]")

    with open(out, "w", encoding="utf-8") as f:
        for o in outputs:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")

    console.log(f"\n🎉 كل حاجة خلصت! الملف جاهز: {out}")


if __name__ == "__main__":
    run()