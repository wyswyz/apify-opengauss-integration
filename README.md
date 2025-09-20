# Apify Actor for OpenGauss Integrations

This project was inspired by and derived from the official `apify/actor-vector-database-integrations` repository. Special thanks to the Apify team for their foundational work.

| Actor                       | Actor badge |
|-----------------------------|---------------------|
| [OpenGauss](https://opengauss.org/) | [![Opengauss integration](https://apify.com/actor-badge?actor=wyswyz/opengauss-integration)](https://apify.com/wyswyz/opengauss-integration) |

#### Vector database integrations (Actors)

The Apify Vector Database Integrations facilitate the transfer of data from Apify Actors to  openGauss vector database. 
This process includes data processing, optional splitting into chunks, embedding computation, and data storage

These integrations support incremental updates, ensuring that only changed data is updated. 
This reduces unnecessary embedding computation and storage operations, making it ideal for search and retrieval augmented generation (RAG) use cases.

## How does it work?

1. Retrieve a dataset as output from an Actor.
2. _[Optional]_ Split text data into chunks using [langchain](https://python.langchain.com).
3. _[Optional]_ Update only changed data.
4. Compute embeddings, e.g. using [OpenAI](https://platform.openai.com/docs/guides/embeddings) or [Cohere](https://cohere.com/embeddings).
5. Save data into the database.

## Supported Vector Embeddings

- [OpenAI](https://platform.openai.com/docs/guides/embeddings)
- [Cohere](https://cohere.com/embeddings)
