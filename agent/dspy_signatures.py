import dspy


# Router: rag or sql or hybrid
class ClassifyRoute(dspy.Signature):
    """Classify the type of question: rag (only docs), sql (only database), hybrid (both)"""
    question: str = dspy.InputField()
    route: str = dspy.OutputField(desc="one of: rag, sql, hybrid", choices=["rag", "sql", "hybrid"])


# NL to SQL
class GenerateSQL(dspy.Signature):
    """Generate correct SQLite SQL using the schema and context"""
    question: str = dspy.InputField()
    schema: str = dspy.InputField(desc="Database schema as text")
    docs_context: str = dspy.InputField(desc="Relevant documents")
    sql: str = dspy.OutputField(desc="Valid executable SQLite query, no markdown")


# Final Answer Synthesis
class SynthesizeAnswer(dspy.Signature):
    """Return exact JSON/number as requested + short explanation + citations"""
    question: str = dspy.InputField()
    format_hint: str = dspy.InputField()
    sql_result: str = dspy.InputField(desc="Result from SQL or docs")
    retrieved_docs: str = dspy.InputField()
    answer: str = dspy.OutputField(desc="Exact match to format_hint, valid JSON or number")
    explanation: str = dspy.OutputField(desc="Maximum 2 sentences")
    citations: str = dspy.OutputField(desc="Comma-separated list like Orders,marketing_calendar.md::chunk0")