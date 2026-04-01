from __future__ import annotations

import json
import os
import tempfile
import unittest

from artifacts import begin_match, RoundResult


class TestArtifacts(unittest.TestCase):
    def test_begin_match_writes_meta_and_optional_events(self):
        with tempfile.TemporaryDirectory() as td:
            ma = begin_match(
                base_dir=td,
                mode="MATCH",
                best_of=3,
                fixed_tick_match=True,
                fps=60,
                controllers={"p1": {"kind": "script", "name": "a"}, "p2": {"kind": "script", "name": "b"}},
                arena={"screen_width": 1000, "screen_height": 600},
                enable_events=True,
            )

            meta_path = os.path.join(ma.out_dir, "meta.json")
            self.assertTrue(os.path.exists(meta_path))
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self.assertEqual(meta["schema"], "openclaw-battle.artifacts.meta.v0")
            self.assertEqual(meta["mode"], "MATCH")
            self.assertEqual(meta["best_of"], 3)
            self.assertTrue(meta["fixed_tick_match"])
            self.assertEqual(meta["fps"], 60)
            self.assertIn("match_id", meta)

            self.assertIsNotNone(ma.events_path)
            self.assertTrue(os.path.exists(ma.events_path))

    def test_finalize_writes_result_schema_and_rounds(self):
        with tempfile.TemporaryDirectory() as td:
            ma = begin_match(
                base_dir=td,
                mode="MATCH",
                best_of=3,
                fixed_tick_match=True,
                fps=60,
                controllers={"p1": {"kind": "script", "name": "a"}, "p2": {"kind": "script", "name": "b"}},
                arena={"screen_width": 1000, "screen_height": 600},
                enable_events=False,
            )

            ma.add_round(
                RoundResult(
                    round=1,
                    winner=1,
                    ticks=100,
                    end_reason="ko",
                    p1_damage=25,
                    p2_damage=10,
                    p1_hits=3,
                    p2_hits=1,
                    avg_distance=123.5,
                )
            )
            ma.add_round(RoundResult(round=2, winner=1, ticks=120, end_reason="timeout"))
            ma.finalize()

            res_path = os.path.join(ma.out_dir, "result.json")
            self.assertTrue(os.path.exists(res_path))
            with open(res_path, "r", encoding="utf-8") as f:
                res = json.load(f)

            self.assertEqual(res["schema"], "openclaw-battle.artifacts.result.v0")
            self.assertEqual(res["winner"], 1)
            self.assertEqual(res["score"]["p1"], 2)
            self.assertEqual(res["score"]["p2"], 0)
            self.assertEqual(len(res["rounds"]), 2)
            self.assertEqual(res["rounds"][0]["round"], 1)
            self.assertEqual(res["rounds"][0]["ticks"], 100)
            self.assertEqual(
                res["rounds"][0]["stats"],
                {
                    "p1_damage": 25,
                    "p2_damage": 10,
                    "p1_hits": 3,
                    "p2_hits": 1,
                    "avg_distance": 123.5,
                },
            )
            self.assertIsNone(res["rounds"][1]["stats"])


if __name__ == "__main__":
    unittest.main()
