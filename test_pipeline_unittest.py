from __future__ import annotations

import json
import os
import tempfile
import unittest

from artifacts import RoundResult, begin_match
from tournament_runner import aggregate_results


class TestPipeline(unittest.TestCase):
    def test_artifacts_to_leaderboard_pipeline(self):
        # End-to-end-ish: write meta/result artifacts, then aggregate into leaderboard.
        with tempfile.TemporaryDirectory() as td:
            base = os.path.join(td, "logs", "matches")
            ma = begin_match(
                base_dir=base,
                mode="MATCH",
                best_of=3,
                fixed_tick_match=True,
                fps=60,
                controllers={
                    "p1": {"kind": "script", "name": "a"},
                    "p2": {"kind": "script", "name": "b"},
                },
                arena={"screen_width": 1000, "screen_height": 600},
                enable_events=False,
            )

            ma.add_round(
                RoundResult(
                    round=1,
                    winner=1,
                    ticks=100,
                    end_reason="ko",
                    p1_damage=7,
                    p2_damage=3,
                    p1_hits=1,
                    p2_hits=2,
                    avg_distance=50.0,
                )
            )
            ma.finalize()

            result_path = os.path.join(ma.out_dir, "result.json")
            self.assertTrue(os.path.exists(result_path))
            # sanity: meta exists too
            self.assertTrue(os.path.exists(os.path.join(ma.out_dir, "meta.json")))

            board = aggregate_results([result_path])
            self.assertEqual(board["schema"], "openclaw-battle.tournament.leaderboard.v2")
            self.assertEqual(board["matches"], 1)
            self.assertEqual(board["players"]["script-a"]["wins"], 1)
            self.assertEqual(board["players"]["script-b"]["losses"], 1)
            self.assertEqual(board["players"]["script-a"]["stats"]["damage_dealt"], 7)


if __name__ == "__main__":
    unittest.main()
