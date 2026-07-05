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
