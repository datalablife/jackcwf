# LangChain RAG Quick Start Guide

**For**: Developers integrating LangChain with Lantern vector database
**Time to Setup**: 5 minutes
**Prerequisites**: Python 3.8+, LangChain, OpenAI API key

---

## ⚡ 5-Minute Setup

### 1. Verify Environment (1 min)

```bash
# Load environment variables
set -a && source .env && set +a

# Validate configuration
python scripts/validate_env.py

# Should output:
# ✅ DATABASE_URL is configured
# ✅ POSTGRES_HOST is configured
# ✅ POSTGRES_PORT is configured
# ✅ POSTGRES_USER is configured
# ✅ POSTGRES_DB is configured
```

### 2. Ensure Schema Exists (1 min)

```bash
# Create tables and indexes (idempotent, safe to run multiple times)
python src/db/setup_lantern_schema.py

# Should output:
# ✅ Lantern Vector Storage Schema Setup Complete!
```

### 3. Test RAG System (1 min)

```bash
# Run comprehensive tests
python src/db/test_lantern_rag.py

# Should show all 6 tests passing
```

### 4. Install Dependencies (1 min)

```bash
pip install langchain openai asyncpg numpy python-dotenv
```

### 5. Create RAG Chain (1 min)

```python
import os
from langchain.vectorstores.pgvector import PGVector
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms.openai import OpenAI
from langchain.chains import RetrievalQA

# Initialize components
embeddings = OpenAIEmbeddings()
vector_store = PGVector(
    connection_string=os.getenv("DATABASE_URL"),
    embedding_function=embeddings,
    collection_name="documents"
)
llm = OpenAI(temperature=0)

# Create RAG chain
rag = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vector_store.as_retriever(search_kwargs={"k": 5})
)

# Query
response = rag.run("What is vector search?")
print(response)
```

---

## 🔄 Common Workflows

### Workflow 1: Add Documents to RAG

```python
from langchain.document_loaders import TextLoader
from langchain.text_splitters import CharacterTextSplitter
from langchain.vectorstores.pgvector import PGVector
from langchain.embeddings.openai import OpenAIEmbeddings

# Load documents
loader = TextLoader("document.txt")
documents = loader.load()

# Split into chunks
splitter = CharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = splitter.split_documents(documents)

# Add to vector store
embeddings = OpenAIEmbeddings()
PGVector.from_documents(
    chunks,
    embeddings,
    connection_string=os.getenv("DATABASE_URL"),
    collection_name="documents"
)

print(f"Added {len(chunks)} chunks to RAG system")
```

### Workflow 2: Query with Metadata Filtering

```python
from langchain.vectorstores.pgvector import PGVector
from langchain.embeddings.openai import OpenAIEmbeddings

# Initialize vector store
embeddings = OpenAIEmbeddings()
vector_store = PGVector(
    connection_string=os.getenv("DATABASE_URL"),
    embedding_function=embeddings,
    collection_name="documents"
)

# Search with filtering
retriever = vector_store.as_retriever(
    search_kwargs={
        "k": 5,  # Return top 5
        "filter": {  # Filter by metadata
            "source": "technical_docs"
        }
    }
)

# Get results
results = retriever.get_relevant_documents("vector search")
for doc in results:
    print(f"- {doc.page_content[:100]}... (source: {doc.metadata.get('source')})")
```

### Workflow 3: Multi-Turn Conversation

```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.llms.openai import OpenAI

# Setup memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Create conversational chain
qa = ConversationalRetrievalChain.from_llm(
    llm=OpenAI(temperature=0),
    retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
    memory=memory
)

# Multi-turn conversation
questions = [
    "What is RAG?",
    "How does it work?",
    "What are the benefits?"
]

for question in questions:
    response = qa({"question": question})
    print(f"Q: {question}")
    print(f"A: {response['answer']}\n")
```

### Workflow 4: Batch Document Ingestion

```python
import asyncio
from langchain.vectorstores.pgvector import PGVector
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document

async def batch_add_documents(documents_list, batch_size=50):
    """Add documents in batches for efficiency"""
    embeddings = OpenAIEmbeddings()

    for i in range(0, len(documents_list), batch_size):
        batch = documents_list[i:i+batch_size]
        print(f"Adding batch {i//batch_size + 1}...")

        PGVector.from_documents(
            batch,
            embeddings,
            connection_string=os.getenv("DATABASE_URL"),
            collection_name="documents"
        )

        # Small delay to avoid overwhelming the server
        await asyncio.sleep(1)

# Usage
documents = [
    Document(page_content=f"Document {i}", metadata={"source": "batch_import"})
    for i in range(1000)
]

asyncio.run(batch_add_documents(documents))
```

### Workflow 5: RAG with Custom Tools

```python
from langchain.agents import Tool, AgentExecutor, initialize_agent, AgentType
from langchain.llms.openai import OpenAI
from langchain.vectorstores.pgvector import PGVector
from langchain.embeddings.openai import OpenAIEmbeddings

# Create custom tool for vector search
def search_documents(query: str) -> str:
    embeddings = OpenAIEmbeddings()
    vector_store = PGVector(
        connection_string=os.getenv("DATABASE_URL"),
        embedding_function=embeddings,
        collection_name="documents"
    )

    results = vector_store.similarity_search(query, k=3)
    return "\n".join([doc.page_content for doc in results])

# Register tool
tools = [
    Tool(
        name="SearchDocuments",
        func=search_documents,
        description="Search the RAG database for relevant documents"
    )
]

# Create agent
agent = initialize_agent(
    tools,
    OpenAI(temperature=0),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Use agent
response = agent.run("Find information about vector databases and explain how they work")
print(response)
```

---

## 🛠️ Configuration Reference

### Environment Variables

```bash
# Database Connection (Required)
DATABASE_URL=postgresql+asyncpg://user:password@host:port/db

# OpenAI API (Required for embeddings)
OPENAI_API_KEY=sk-...

# Optional: Fine-tune vector store behavior
VECTOR_DIM=1536              # Embedding dimension (OpenAI)
SEARCH_K=5                   # Default number of results
SIMILARITY_THRESHOLD=0.7     # Minimum similarity score
```

### Search Methods

```python
# 1. Similarity search (cosine distance)
results = vector_store.similarity_search(
    "vector search",
    k=5,
    distance_metric="cosine"
)

# 2. Similarity search with score
results = vector_store.similarity_search_with_score(
    "vector search",
    k=5
)

# 3. Maximum Marginal Relevance (MMR)
results = vector_store.max_marginal_relevance_search(
    "vector search",
    k=5,
    fetch_k=20  # Fetch more candidates, return diverse results
)

# 4. By vector directly
results = vector_store.similarity_search_by_vector(
    embedding_vector=[...],
    k=5
)
```

---

## 📊 Performance Tips

### Tip 1: Use Connection Pooling

```python
import asyncpg
from contextlib import asynccontextmanager

class RAGPool:
    def __init__(self, connection_string: str, min_size=5, max_size=20):
        self.pool = None
        self.connection_string = connection_string
        self.min_size = min_size
        self.max_size = max_size

    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=self.min_size,
            max_size=self.max_size
        )

    @asynccontextmanager
    async def acquire(self):
        async with self.pool.acquire() as conn:
            yield conn

# Usage
pool = RAGPool(os.getenv("DATABASE_URL"))
# Then use pool.acquire() for connections
```

### Tip 2: Batch Queries

```python
# ❌ Slow: 100 queries in sequence
for doc_id in doc_ids:
    result = search(doc_id)

# ✅ Fast: Batch process
batch_size = 20
for i in range(0, len(doc_ids), batch_size):
    batch = doc_ids[i:i+batch_size]
    results = [search(doc) for doc in batch]
```

### Tip 3: Cache Embeddings

```python
from functools import lru_cache
from langchain.embeddings.openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()

@lru_cache(maxsize=1000)
def cached_embed(text: str):
    return embeddings.embed_query(text)

# First call: computes embedding
# Subsequent calls: returns cached value
embedding = cached_embed("vector database")
```

### Tip 4: Preload for Warm Queries

```python
# When application starts, warm up the system
def warmup_rag():
    """Preload indexes and connections"""
    queries = [
        "what is RAG",
        "vector search",
        "langchain tutorial"
    ]

    for query in queries:
        vector_store.similarity_search(query, k=1)

    print("RAG system warmed up ✅")

# Call on app startup
warmup_rag()
```

---

## 🐛 Troubleshooting

### Issue: "DATABASE_URL not found"

```bash
# Fix: Load environment variables
set -a && source .env && set +a
python your_script.py
```

### Issue: "PGVector not found"

```bash
# Fix: Install langchain with all dependencies
pip install langchain[postgres] openai
```

### Issue: "Connection refused"

```bash
# Check: Is PostgreSQL running?
python scripts/validate_env.py

# Check: Firewall allows access to 47.79.87.199:5432
# Check: .env has correct credentials
```

### Issue: "Slow queries"

```bash
# Run performance test
python src/db/test_lantern_rag.py

# Check: Network latency
ping 47.79.87.199

# Optimize: See LANTERN_PERFORMANCE_ANALYSIS.md
```

### Issue: "Memory usage high"

```python
# Reduce batch size
batch_size = 10  # Instead of 50

# Reduce retrieval results
search_kwargs={"k": 3}  # Instead of 10

# Use lazy loading
documents = loader.load_and_split(
    text_splitter=CharacterTextSplitter(chunk_size=500)
)
```

---

## 📚 Additional Resources

- **Full Deployment Guide**: `docs/POSTGRESQL_DEPLOYMENT_GUIDE.md`
- **Performance Analysis**: `docs/LANTERN_PERFORMANCE_ANALYSIS.md`
- **Security Best Practices**: `docs/SECURE_DATABASE_SETUP.md`
- **LangChain Documentation**: https://python.langchain.com/
- **Lantern GitHub**: https://github.com/lanterndata/lantern
- **OpenAI API Docs**: https://platform.openai.com/docs

---

## ✅ Verification Checklist

Before deploying to production:

- [ ] Environment variables loaded correctly
- [ ] Database connection verified
- [ ] RAG tests all passing
- [ ] Embeddings working with OpenAI API
- [ ] RAG chains returning expected results
- [ ] Performance acceptable for your use case
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Security review completed

---

**Last Updated**: 2025-11-18
**Status**: ✅ Production Ready

