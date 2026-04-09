# LangChain Docs Assistant

## Project Description
LangChain Docs Assistant is an interactive AI-powered chatbot designed to help users query and explore the LangChain documentation effortlessly. Built with Streamlit on the frontend and leveraging LangChain’s advanced language models and vector search capabilities on the backend, this assistant delivers accurate and contextually relevant answers sourced from LangChain’s comprehensive docs.

---

## Project Structure

```
LangChain Docs Assistant/
├── backend/              # Core backend logic and AI interactions (2 files)
├── chroma_db/            # Vector database setup and interactions (1 file)
├── d0f42a40-51cb-41a0-b8da-1222d40dc503/  # Presumably project-specific resources or data (4 files)
├── api/                  # API routes, middleware, and authentication (3 files)
├── auth/                 # Authentication mechanisms (3 files)
├── database/             # Database models and operations (3 files)
├── payments/             # Payment processing and handling (3 files)
├── utils/                # Utility functions and helpers (3 files)
├── app.py                # Streamlit frontend app
├── main.py               # Alternative or extended Streamlit interface
├── ingestion.py          # Document ingestion & vectorization logic
├── logger.py             # Colored logging utility for better CLI feedback
├── consts.py             # Project-wide constants
├── backend/core.py       # Primary backend logic including LLM orchestration
├── backend/__init__.py   # Backend package initialization
└── notebooks/            # Tutorial and demo Jupyter notebooks related to Tavily tools
```

---

## Main Features and Purpose

- **Interactive Chat Interface:** Users can ask any question related to LangChain documentation and receive contextual replies in real-time.
- **AI-powered Context Retrieval:** Utilizes OpenAI embeddings combined with Pinecone vector search for precise document retrieval.
- **Robust Backend Engine:** Leverages LangChain’s state-of-the-art language models for generating human-like and relevant answers.
- **Document Ingestion Pipeline:** Processes LangChain docs with AST and text chunking to build a rich vector database for querying.
- **Session Management:** Maintains chat history during sessions to support ongoing conversations.
- **Extensible Architecture:** Modular design with clear separation of API, auth, payment, and utility components.
- **Real-time Feedback:** Built-in spinner indicators during processing to improve UX.

---

## Key Files and Their Roles

- **app.py**  
  The main Streamlit application providing the chat interface. Manages the UI, user input, message history, and triggers the backend for processing questions.

- **main.py**  
  Alternate or extended Streamlit interface with additional UI features like session clearing and source document listing.

- **backend/core.py**  
  Contains the core backend logic responsible for querying the vector store, interfacing with the language model, and composing the assistant’s responses.

- **ingestion.py**  
  Handles document processing and ingestion. Extracts contextual chunks from source code files and uploads embeddings into the vector database.

- **logger.py**  
  Provides colored logging utilities to improve readability of logs and system feedback during execution.

- **consts.py**  
  Defines various global constants used across the project, such as the vector index name.

- **api/**  
  Implements API endpoints and middleware including authentication, rate limiting, and other request handlers.

- **auth/**  
  Authentication logic including login and token management.

- **payments/**  
  Handles payment workflows and integrations, likely for premium features or usage plans.

- **chroma_db/**  
  Vector database interfaces and setup scripts.

- **utils/**  
  Miscellaneous utility functions supporting various functionalities across modules.

- **notebooks/**  
  Educational materials demonstrating related tools and advanced usages in LangChain ecosystem.

---

## Installation and Setup

### Prerequisites
- Python 3.8+
- Access to OpenAI API keys
- Pinecone API key and index setup
- `streamlit` and other dependencies (see requirements)

### Installation

1. **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd langchain-docs-assistant
    ```

2. **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    .\venv\Scripts\activate   # Windows
    ```

3. **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Setup environment variables:**  
   Create a `.env` file in the root directory with your API keys and configurations:
    ```
    OPENAI_API_KEY=your_openai_api_key
    PINECONE_API_KEY=your_pinecone_api_key
    PINECONE_ENVIRONMENT=your_pinecone_environment
    ```

5. **Ingest Documentation:**
    Run the ingestion script to process LangChain documentation and populate the vector store:
    ```bash
    python ingestion.py
    ```

---

## Usage

### Starting the Assistant

Launch the Streamlit app locally:

```bash
streamlit run app.py
```

The app UI will open in your browser at `http://localhost:8501`, presenting you with a chat interface to ask questions about LangChain documentation.

### Chat Interaction

- Type your question about LangChain in the input box.
- The assistant retrieves relevant documentation context using vector search.
- The language model formulates a precise, helpful response displayed in the chat history.
- Use the sidebar in `main.py` (if used) to clear chat sessions.

---

## Contribution

Contributions and feedback are welcome! Please ensure code quality and test new features before submitting pull requests.

---

## License

[MIT License](LICENSE)

---

## Contact

For questions or support, please open an issue or contact the maintainer.