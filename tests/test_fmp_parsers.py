import unittest

from omni_signal.fmp_parsers import (
    parse_analyst_estimates,
    parse_price_target_consensus,
    parse_price_target_summary,
    parse_ratings_snapshot,
)


class TestFMPParsers(unittest.TestCase):
    def test_parse_price_target_consensus_list_payload(self) -> None:
        payload = [
            {
                "symbol": "NVDA",
                "price": 100,
                "consensusPriceTarget": 150,
                "highPriceTarget": 180,
                "lowPriceTarget": 90,
                "medianPriceTarget": 145,
                "numberOfAnalysts": 42,
            }
        ]
        parsed = parse_price_target_consensus(payload)
        self.assertEqual(parsed["current_price"], 100)
        self.assertEqual(parsed["consensus_price_target"], 150)
        self.assertEqual(parsed["high_price_target"], 180)
        self.assertEqual(parsed["low_price_target"], 90)
        self.assertEqual(parsed["median_price_target"], 145)
        self.assertEqual(parsed["analyst_count"], 42)

    def test_parse_price_target_summary_dict_payload(self) -> None:
        payload = {
            "symbol": "NVDA",
            "price": 100,
            "averagePriceTarget": 155,
            "previousPriceTarget": 150,
            "analystsCount": 38,
        }
        parsed = parse_price_target_summary(payload)
        self.assertEqual(parsed["current_price"], 100)
        self.assertEqual(parsed["average_price_target"], 155)
        self.assertEqual(parsed["previous_price_target"], 150)
        self.assertEqual(parsed["analyst_count"], 38)

    def test_parse_analyst_estimates_tracks_revision_direction(self) -> None:
        payload = {
            "data": [
                {
                    "period": "Q1",
                    "calendarYear": "2026",
                    "estimatedEpsAvg": 5.5,
                    "estimatedEpsAvgPrior": 5.0,
                    "estimatedRevenueAvg": 100,
                    "estimatedRevenueAvgPrior": 95,
                }
            ]
        }
        parsed = parse_analyst_estimates(payload)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["estimated_eps_avg"], 5.5)
        self.assertEqual(parsed[0]["estimated_eps_avg_prior"], 5.0)
        self.assertEqual(parsed[0]["revision_direction"], "up")

    def test_parse_ratings_snapshot_handles_nested_list(self) -> None:
        payload = [
            {
                "rating": "buy",
                "score": 77,
                "dcfScore": 70,
                "roeScore": 65,
            }
        ]
        parsed = parse_ratings_snapshot(payload)
        self.assertEqual(parsed["rating"], "buy")
        self.assertEqual(parsed["rating_score"], 77)
        self.assertEqual(parsed["dcf_score"], 70)
        self.assertEqual(parsed["roe_score"], 65)
