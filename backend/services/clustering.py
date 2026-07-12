# Cosine similarity measures the angle between two vectors, not their distance — this matters because it ignores text length differences and focuses purely on meaning/direction.

# We combine title + description before embedding, since titles alone are often too short to capture full context.

# The clustering logic here is simple and greedy: each new article checks against existing cluster "representatives" (the first article's embedding in each cluster); if similarity crosses the threshold, it joins that cluster; otherwise it starts a new one. This is O(n²) but totally fine at our scale (handful of articles per fetch cycle).

# threshold=0.75 is directly from your spec — a reasonable starting point. We can tune this once we see real results (too low = unrelated articles merge; too high = duplicate stories don't merge).

import numpy as np
from services.embeddings import get_embeddings_batch

def cosine_similarity(vec_a, vec_b) -> float:
  """Measures how 'close' two vectors point, from -1 to 1.
  1= identical meaning, 0=unrelated, -1= opposite meaning."""

  a = np.array(vec_a)
  b = np.array(vec_b)

  return float(np.dot(a,b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# linalg.norm is the vector length (magnitude) — we divide by it to normalize the dot product, so we only measure direction/meaning, not length.

def cluster_articles(articles: list[dict], threshold=0.75) -> list[list[dict]]:
    """
    Groups articles into clusters based on title+description similarity.
    Returns a list of clusters, where each cluster is a list of article dicts.
    """
    if not articles:
       return[]

    # Combine title + description for each article, then get embeddings in a single batch call.

    texts= [f"{a['title']} {a.get('description', '')}" for a in articles]
    embeddings = get_embeddings_batch(texts)

    clusters: list[list[int]] = []  # Each cluster is a list of article indices ( stores article INDEXES per cluster)

    # cluster_embeddings : list[list[float]] = []  # Each cluster's representative embedding (the first article's embedding in that cluster)
    cluster_embeddings: list[np.ndarray] = []  # now stores the running centroid, not just the first embedding

    # clusters = [
    # [0, 3],   # Apple-related articles
    # [1, 4],   # Cricket-related articles
    # [2]       # AI article
    # ]

    # cluster_embeddings = [
    #     [0.12, -0.53, 0.81, ...],   # embedding for Cluster 1
    #     [-0.40, 0.91, 0.10, ...],   # embedding for Cluster 2
    #     [0.65, 0.22, -0.71, ...]    # embedding for Cluster 3
    # ]

    for i, emb in enumerate(embeddings):
        emb_arr = np.array(emb)
        placed = False
        for c_idx, c_emb in enumerate(cluster_embeddings):
            similarity = cosine_similarity(emb, c_emb)
            if similarity >= threshold:
                clusters[c_idx].append(i)
                # Recompute centroid: average of all article embeddings now in this cluster
                member_embeddings = [np.array(embeddings[idx]) for idx in clusters[c_idx]]
                cluster_embeddings[c_idx] = np.mean(member_embeddings, axis=0)
                placed = True
                break
        if not placed:
            clusters.append([i])
            cluster_embeddings.append(emb)

 # Convert index-clusters back into article-clusters
    return [[articles[i] for i in cluster] for cluster in clusters]

if __name__ == "__main__":
    from services.news_fetcher import fetch_tech_news

    articles = fetch_tech_news(max_articles=10)
    clusters = cluster_articles(articles)

    print(f"Total articles: {len(articles)}")
    print(f"Total clusters: {len(clusters)}\n")

    for i, cluster in enumerate(clusters):
        print(f"--- Cluster {i+1} ({len(cluster)} article(s)) ---")
        for a in cluster:
            print(" -", a["title"])
        print()
