import unittest
from backend.rag.vector_store import VectorStore
from backend.rag.embeddings import EmbeddingEngine, cosine_similarity

class TestRAG(unittest.TestCase):
    def setUp(self):
        self.vs = VectorStore()

    def test_embeddings_cosine_similarity(self):
        engine = EmbeddingEngine(vector_dim=128)
        v1 = engine.get_local_embedding("refund return policy")
        v2 = engine.get_local_embedding("money back guarantee and returns")
        v3 = engine.get_local_embedding("aerospace rocket propulsion fuel")

        sim_related = cosine_similarity(v1, v2)
        sim_unrelated = cosine_similarity(v1, v3)

        self.assertGreater(sim_related, sim_unrelated)

    def test_vector_store_search(self):
        results = self.vs.search("30-day return policy", top_k=2)
        self.assertTrue(len(results) > 0)
        top_title = results[0]["title"]
        self.assertIn("Return", top_title)

    def test_vector_store_add_and_delete(self):
        doc_id = self.vs.add_document(
            title="Test Warranty Guide",
            category="Warranty",
            content="This is a test article covering lifetime replacement guarantees for test products."
        )
        self.assertTrue(doc_id.startswith("KB-"))

        # Verify search finds it
        res = self.vs.search("lifetime replacement guarantees", top_k=1)
        self.assertTrue(len(res) > 0)

        # Cleanup
        self.vs.delete_document(doc_id)

if __name__ == "__main__":
    unittest.main()
