# We load the model once at import time (_model = SentenceTransformer(...)), not inside the function. Loading it is slow (~1-2 sec); if we reloaded it on every call, everything would crawl. This way it loads once when the server starts, then stays in memory.

# all-MiniLM-L6-v2 outputs a 384-number vector per piece of text. Two texts about similar topics will have vectors that point in similar directions — that's what cosine similarity (Step 7) will measure.

# get_embeddings_batch exists because we'll typically have 10+ articles at once — batching is meaningfully faster than one-by-one.

from sentence_transformers import SentenceTransformer
model= SentenceTransformer('all-MiniLM-L6-v2')        #stored in cache
# this is like hiring an expert translator
# popular embedding model:fast, small(~80mb),good quality,free
def get_embedding(text: str):
  """
    Convert a piece of text into an embedding vector (list of floats).
    Similar meanings produce similar vectors.
    """
  embedding=model.encode(text)
  return embedding.tolist()  #convert numpy array to list of floats: easy to send as json

def get_embeddings_batch(texts: list[str]):
    """
    Convert multiple texts into embeddings in one batch call — faster than
    calling get_embedding() in a loop, since the model processes them together.
    """
    embeddings = model.encode(texts)
    return [e.tolist() for e in embeddings]


#                   Program Starts
#                         │
#                         ▼
#       Load SentenceTransformer Model (once)
#                         │
#         ┌───────────────┴───────────────┐
#         │                               │
#         ▼                               ▼
# get_embedding(text)        get_embeddings_batch(texts)
#      one string                  list of strings
# (when user seaches topic)  (for multiple article embeddings)
#         │                               │
#         ▼                               ▼
#    model.encode(text)          model.encode(texts)
#         │                               │
#         ▼                               ▼
#  NumPy array (384 floats)      List of NumPy arrays
#         │                               │
#         ▼                               ▼
#     .tolist()                  Convert each to list
#         │                               │
#         └───────────────┬───────────────┘
#                         ▼
#          Return JSON-friendly Python list(s)

if __name__ == "__main__":
    vec = get_embedding("Apple unveils new AI chip")
    print("Vector length:", len(vec))
    print("First 5 values:", vec[:5])
