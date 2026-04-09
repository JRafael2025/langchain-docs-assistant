import os
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langgraph.prebuilt import create_react_agent

load_dotenv()

# Initialize embeddings (same as ingestion.py)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Initialize vector store
vectorstore = PineconeVectorStore(
    index_name="langchain-doc-index", embedding=embeddings
)

# BUG FIX #3: "gpt-5.2" does not exist; use a valid model name like "gpt-4o"
model = ChatOpenAI(model="gpt-4o")


@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve relevant documentation to help answer user queries about LangChain."""
    # BUG FIX #4: k must be passed to as_retriever() via search_kwargs, not to invoke()
    retrieved_docs = vectorstore.as_retriever(search_kwargs={"k": 4}).invoke(query)

    # Serialize documents for the model
    serialized = "\n\n".join(
        (f"Source: {doc.metadata.get('source', 'Unknown')}\n\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )

    # Return both serialized content and raw documents
    return serialized, retrieved_docs


def run_llm(query: str) -> Dict[str, Any]:
    """
    Run the RAG pipeline to answer a query using retrieved documentation.

    Args:
        query: The user's question

    Returns:
        Dictionary containing:
            - answer: The generated answer
            - context: List of retrieved documents
    """
    system_prompt = (
        "You are a helpful AI assistant that answers questions about LangChain documentation. "
        "You have access to a tool that retrieves relevant documentation. "
        "Use the tool to find relevant information before answering questions. "
        "Always cite the sources you use in your answers. "
        "If you cannot find the answer in the retrieved documentation, say so."
    )

    # BUG FIX #2: create_agent does not exist; use create_react_agent from langgraph.prebuilt
    # BUG FIX #1: langchain.agents / langchain.chat_models / langchain.messages / langchain.tools
    #             are wrong import paths; fixed to langchain_core, langchain_openai, langgraph
    agent = create_react_agent(model, tools=[retrieve_context], prompt=system_prompt)

    # Build messages list
    messages = [{"role": "user", "content": query}]

    # Invoke the agent
    response = agent.invoke({"messages": messages})

    # Extract the answer from the last AI message
    answer = response["messages"][-1].content

    # Extract context documents from ToolMessage artifacts
    context_docs = []
    for message in response["messages"]:
        if isinstance(message, ToolMessage) and hasattr(message, "artifact"):
            if isinstance(message.artifact, list):
                context_docs.extend(message.artifact)

    # BUG FIX #6: Return context_docs (Document objects) so main.py's _format_sources works correctly
    return {
        "answer": answer,
        "context": context_docs,
    }


# BUG FIX #5: Removed dangling result = run_llm(...) line that was outside any block
if __name__ == "__main__":
    print("\n🔎 TESTING RETRIEVAL...\n")

    retriever = vectorstore.as_retriever()
    docs = retriever.invoke("What is LangChain?")

    print(f"Documents returned: {len(docs)}\n")

    if docs:
        print("First document preview:\n")
        print(docs[0].page_content[:500])
