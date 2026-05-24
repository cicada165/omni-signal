import unittest

from omni_signal.scoring import score_snapshot


class TestScoring(unittest.TestCase):
    def test_complete_data_scores_reasonably(self) -> None:
        snapshot = {
            "ticker": "NVDA",
            "theme_names": ["memory_hbm", "semiconductor_cycle"],
            "price_target": {"price": 100, "consensusPriceTarget": 150},
            "price_target_summary": {"averagePriceTarget": 155},
            "analyst_estimates": [
                {"estimatedEpsAvg": 5.5, "estimatedEpsAvgPrior": 5.0}
            ],
            "ratings_snapshot": {"overallRating": "buy", "score": 78},
        }
        result = score_snapshot(snapshot)
        self.assertEqual(result["ticker"], "NVDA")
        self.assertGreaterEqual(result["score"], 70)
        self.assertIn(result["confidence"], {"medium", "high"})
        self.assertIn("price target upside detected", result["signals"])
        self.assertIn("ratings snapshot favorable", result["signals"])
        self.assertIn("estimate revisions trending upward", result["signals"])

    def test_missing_data_is_handled(self) -> None:
        snapshot = {
            "ticker": "MU",
            "theme_names": ["memory_hbm"],
            "price_target": {},
            "price_target_summary": {},
            "analyst_estimates": [],
            "ratings_snapshot": {},
        }
        result = score_snapshot(snapshot)
        self.assertEqual(result["ticker"], "MU")
        self.assertEqual(result["confidence"], "low")
        self.assertLess(result["score"], 50)
        self.assertIn("price target data incomplete", result["signals"])
        self.assertIn("ratings snapshot missing", result["signals"])
        self.assertIn("estimate data incomplete", result["signals"])
