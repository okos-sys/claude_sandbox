from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

mcp = FastMCP("DocumentMCP", log_level="ERROR")


docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

# Business rule enforced in code (not in a prompt): these documents can never be edited.
PROTECTED_DOCS = {"deposition.md"}


# ---------- TOOLS (the model decides when to use them) ----------

@mcp.tool(
    name="read_doc_contents",
    description=(
        "Read the full text of a document stored on the document server. "
        "All documents on this server (.pdf, .docx, .md, .txt) are stored as plain text, "
        "so this tool works for any of them. Use the exact document ID, e.g. 'report.pdf'. "
        "Use this before editing, to see the exact current text."
    ),
)
def read_document(
    doc_id: str = Field(description="Id of the document to read"),
):
    if doc_id not in docs:
        raise ValueError(
            f"errorCategory: validation | isRetryable: false | "
            f"Document '{doc_id}' does not exist. Available documents: {', '.join(docs)}"
        )
    return docs[doc_id]


@mcp.tool(
    name="edit_document",
    description=(
        "Edit a document stored on the document server by replacing an exact piece of text "
        "with new text. All documents on this server (.pdf, .docx, .md, .txt) are stored as "
        "plain text, so any of them can be edited with this tool, regardless of the file extension. "
        "Use the exact document ID, e.g. 'report.pdf'. The old text must match exactly; "
        "if unsure, call read_doc_contents first."
    ),
)
def edit_document(
    doc_id: str = Field(description="Id of the document that will be edited"),
    old_str: str = Field(description="The text to replace. Must match exactly, including whitespace."),
    new_str: str = Field(description="The new text to insert in place of the old text."),
):
    if doc_id not in docs:
        raise ValueError(
            f"errorCategory: validation | isRetryable: false | "
            f"Document '{doc_id}' does not exist. Available documents: {', '.join(docs)}"
        )
    if doc_id in PROTECTED_DOCS:
        raise ValueError(
            f"errorCategory: permission | isRetryable: false | "
            f"Document '{doc_id}' is a legal record and is read-only. "
            "Do not retry. Tell the user that changes require approval from the legal team."
        )
    docs[doc_id] = docs[doc_id].replace(old_str, new_str)
    return f"Document {doc_id} updated."


# ---------- RESOURCES (the application decides when to use them) ----------

@mcp.resource("docs://documents", mime_type="application/json")
def list_docs() -> list[str]:
    return list(docs.keys())


@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
def fetch_doc(doc_id: str) -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    return docs[doc_id]


# ---------- PROMPTS (the user decides when to use them) ----------

@mcp.prompt(
    name="format",
    description="Rewrites the contents of the document in Markdown format.",
)
def format_document(
    doc_id: str = Field(description="Id of the document to format"),
) -> list[base.Message]:
    prompt = f"""
Your goal is to reformat a document to be written with markdown syntax.

The id of the document you need to reformat is:
<document_id>
{doc_id}
</document_id>

Add in headers, bullet points, tables, etc as necessary. Feel free to add in extra text,
but don't change the meaning of the report.
Use the 'edit_document' tool to edit the document. After the document has been edited,
respond with the final version of the doc. Don't explain your changes.
"""
    return [base.UserMessage(prompt)]


@mcp.prompt(
    name="summarize",
    description="Summarizes the contents of a document.",
)
def summarize_document(
    doc_id: str = Field(description="Id of the document to summarize"),
) -> list[base.Message]:
    prompt = f"""
Your goal is to summarize the contents of a document.

The id of the document you need to summarize is:
<document_id>
{doc_id}
</document_id>

Use the 'read_doc_contents' tool to read the document.
Write a concise summary in 2-3 bullet points.
Only include facts that are present in the document. Do not invent details.
"""
    return [base.UserMessage(prompt)]


if __name__ == "__main__":
    mcp.run(transport="stdio")