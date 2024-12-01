from whoosh import scoring
from whoosh.index import open_dir
import numpy as np

class PageRankWeighting(scoring.WeightingModel):
    """
    Implements the PageRank weighting model, which combines a base weighting model with page rank values.
    """
    def __init__(self):
        """
        :param pagerank_dict: A dictionary mapping docnums to their page rank values.
        :param base_weighting: An optional base weighting model, e.g., scoring.TF_IDF().
        """
        pageranks = np.load("pagerank/data/pageranks.dat")
        self.pagerank_dict = {i: pagerank for i, pagerank in enumerate(pageranks)}
        self.base_weighting = scoring.BM25F()
    
    def scorer(self, searcher, fieldname, text, qf=1):
        base_scorer = self.base_weighting.scorer(searcher, fieldname, text, qf)
        return PageRankScorer(base_scorer, self.pagerank_dict)

class PageRankScorer(scoring.BaseScorer):
    def __init__(self, base_scorer, pagerank_dict):
        """
        :param base_scorer: The base scorer to use for term relevance.
        :param pagerank_dict: A dictionary mapping docnums to their page rank values.
        """
        self.base_scorer = base_scorer
        self.pagerank_dict = pagerank_dict
        self.max = max(self.pagerank_dict.values())
        # print([(i, rank) for i, rank in self.pagerank_dict.items()][:5])

    # Return the maximum quality score
    def max_quality(self):
        return self.base_scorer.max_quality() * self.max

    def score(self, matcher):
        # Base score using term relevance
        base_score = self.base_scorer.score(matcher)
        # Retrieve page rank for the current document
        docnum = matcher.id()
        pagerank = self.pagerank_dict.get(docnum, 0)
        # Combine the scores; you can adjust the weighting of page rank here
        max_base_score = self.base_scorer.max_quality()
        alpha = 0.3
        combined_score = (alpha * (base_score/max_base_score)) + ((1 - alpha) * (pagerank/0.05))
        return combined_score
