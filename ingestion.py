import ast
import asyncio
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from logger import (Colors, log_error, log_header, log_info, log_success,
                    log_warning)

load_dotenv()

CODEBASE_PATH = "./fake_codebase"
SUPPORTED_EXTENSIONS = {".py"}

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    show_progress_bar=False,
    chunk_size=50,
    retry_min_seconds=10,
)
vectorstore = PineconeVectorStore(
    index_name="langchain-doc-index", embedding=embeddings
)


def extract_chunks_from_file(file_path: Path) -> List[Document]:
    """Parse a Python file with AST and extract functions/classes as individual documents."""
    documents = []

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as e:
        log_warning(f"AST Parser: Could not parse {file_path} — {e}")
        return []

    source_lines = source.splitlines()
    relative_path = str(file_path)

    for node in ast.walk(tree):
        # Extract top-level functions and classes
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue

        start_line = node.lineno
        end_line = node.end_lineno

        # Grab the raw source lines for this node
        chunk_lines = source_lines[start_line - 1 : end_line]
        chunk_source = "\n".join(chunk_lines)

        # Determine node type label
        if isinstance(node, ast.ClassDef):
            kind = "class"
        elif isinstance(node, ast.AsyncFunctionDef):
            kind = "async function"
        else:
            kind = "function"

        # Build a rich content block the LLM can cite
        content = (
            f"Source: {relative_path} — {kind} `{node.name}` (lines {start_line}–{end_line})\n\n"
            f"{chunk_source}"
        )

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": relative_path,
                    "name": node.name,
                    "type": kind,
                    "start_line": start_line,
                    "end_line": end_line,
                },
            )
        )

    log_info(
        f"AST Parser: Extracted {len(documents)} chunks from {relative_path}",
        Colors.DARKCYAN,
    )
    return documents


def collect_all_chunks(codebase_path: str) -> List[Document]:
    """Recursively walk the codebase and extract AST chunks from every supported file."""
    log_header("AST PARSING PHASE")
    all_docs = []
    root = Path(codebase_path)

    python_files = [
        p for p in root.rglob("*") if p.suffix in SUPPORTED_EXTENSIONS and p.is_file()
    ]

    log_info(
        f"📂 File Scanner: Found {len(python_files)} Python files under {codebase_path}",
        Colors.PURPLE,
    )

    for file_path in python_files:
        chunks = extract_chunks_from_file(file_path)
        all_docs.extend(chunks)

    log_success(
        f"AST Parser: Finished — {len(all_docs)} total chunks from {len(python_files)} files"
    )
    return all_docs


async def index_documents_async(documents: List[Document], batch_size: int = 50):
    """Process documents in batches asynchronously."""
    log_header("VECTOR STORAGE PHASE")
    log_info(
        f"📚 VectorStore Indexing: Preparing to add {len(documents)} documents to vector store",
        Colors.DARKCYAN,
    )

    batches = [
        documents[i : i + batch_size] for i in range(0, len(documents), batch_size)
    ]

    log_info(
        f"📦 VectorStore Indexing: Split into {len(batches)} batches of {batch_size} documents each"
    )

    async def add_batch(batch: List[Document], batch_num: int):
        try:
            await vectorstore.aadd_documents(batch)
            log_success(
                f"VectorStore Indexing: Successfully added batch {batch_num}/{len(batches)} ({len(batch)} documents)"
            )
        except Exception as e:
            log_error(f"VectorStore Indexing: Failed to add batch {batch_num} — {e}")
            return False
        return True

    tasks = [add_batch(batch, i + 1) for i, batch in enumerate(batches)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful = sum(1 for result in results if result is True)

    if successful == len(batches):
        log_success(
            f"VectorStore Indexing: All batches processed successfully! ({successful}/{len(batches)})"
        )
    else:
        log_warning(
            f"VectorStore Indexing: Processed {successful}/{len(batches)} batches successfully"
        )


async def main():
    """Main async function to orchestrate the entire pipeline."""
    log_header("CODEBASE INGESTION PIPELINE")

    # Step 1 — Parse the codebase with AST
    all_docs = collect_all_chunks(CODEBASE_PATH)

    if not all_docs:
        log_warning("No chunks extracted. Check that CODEBASE_PATH exists and contains .py files.")
        return

    # Step 2 — Index into Pinecone
    await index_documents_async(all_docs, batch_size=50)

    log_header("PIPELINE COMPLETE")
    log_success("🎉 Codebase ingestion pipeline finished successfully!")
    log_info("📊 Summary:", Colors.BOLD)
    log_info(f"   • Files scanned: {CODEBASE_PATH}")
    log_info(f"   • Chunks indexed: {len(all_docs)}")


if __name__ == "__main__":
    asyncio.run(main())
