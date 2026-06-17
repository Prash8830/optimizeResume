import math
import re
from collections import Counter


class BM25:
    """
    BM25 Okapi implementation for sparse keyword scoring.
    Used alongside ChromaDB cosine for hybrid search.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: list[list[str]] = []
        self.doc_freqs: list[Counter] = []
        self.idf: dict[str, float] = {}
        self.avgdl: float = 0.0
        self.n: int = 0

    def fit(self, documents: list[str]) -> "BM25":
        self.corpus = [self._tokenize(doc) for doc in documents]
        self.n = len(self.corpus)
        self.avgdl = sum(len(doc) for doc in self.corpus) / self.n if self.n else 1

        self.doc_freqs = [Counter(doc) for doc in self.corpus]

        df: Counter = Counter()
        for doc in self.corpus:
            for term in set(doc):
                df[term] += 1

        self.idf = {
            term: math.log((self.n - freq + 0.5) / (freq + 0.5) + 1)
            for term, freq in df.items()
        }
        return self

    def get_scores(self, query_terms: list[str]) -> list[float]:
        scores = [0.0] * self.n
        query_tokens = []
        for term in query_terms:
            query_tokens.extend(self._tokenize(term))

        for term in query_tokens:
            if term not in self.idf:
                continue
            idf = self.idf[term]
            for i, doc in enumerate(self.corpus):
                tf = self.doc_freqs[i].get(term, 0)
                dl = len(doc)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                scores[i] += idf * numerator / denominator

        # Normalize to [0, 1]
        max_score = max(scores) if scores else 1.0
        if max_score > 0:
            scores = [s / max_score for s in scores]
        return scores

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"\b[a-z0-9]+\b", text.lower())
