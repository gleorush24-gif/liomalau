# services/embedder.py
#
# LESSON: embeddings + why RAG works
#
# An embedding turns text into a list of ~1536 numbers (a vector).
# The magic: semantically similar text produces vectors that are
# mathematically "close" to each other (measured by cosine similarity).
#
# Example:
#   embed("settlements violate international law")
#   embed("Article 49 Geneva Convention prohibits population transfer")
#   → these two vectors will be close, even though they share no words
#
# This is how lioMalau finds relevant precedents without keyword matching.
# The judge understands *meaning*, not just string overlap.

from openai import AsyncOpenAI
from config import get_settings

settings = get_settings()

# AsyncOpenAI is the async version of the client — non-blocking API calls
_client = AsyncOpenAI(api_key=settings.openai_api_key)


async def embed_text(text: str) -> list[float]:
    """
    Convert a string into a 1536-dimensional vector.
    Returns a plain Python list of floats.
    """
    # Clean the text — embeddings are sensitive to leading/trailing whitespace
    text = text.strip().replace("\n", " ")

    response = await _client.embeddings.create(
        model=settings.embedding_model,
        input=text,
        # dimensions= only works with text-embedding-3-* models
        # it lets you shrink the vector (cheaper storage) at a slight accuracy cost
    )

    # response.data is a list — we sent one string so we get one embedding back
    return response.data[0].embedding   # list of 1536 floats


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed multiple texts in a single API call (much cheaper than one-by-one).
    Use this when seeding the database with precedents.
    """
    texts = [t.strip().replace("\n", " ") for t in texts]

    response = await _client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )

    # Sort by index to guarantee order matches input order
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
