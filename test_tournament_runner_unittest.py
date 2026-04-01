from __future__ import annotations

import json
import os
import tempfile
import unittest

from tournament_runner import aggregate_results


class TestTournamentRunner(unittest.TestCase):
    def test_aggregate_results_keys_by_controller_identity_from_meta(self):
        with tempfile.TemporaryDirectory() as td:
            result_paths = []

            def write_match(idx: int, *, winner, p1_kind: str, p1_name: str, p2_kind: str, p2_name: str):
                mdir = os.path.join(td, f"m{idx}")
                os.makedirs(mdir, exist_ok=True)
                with open(os.path.join(mdir, "meta.json"), "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "controllers": {
                                "p1": {"kind": p1_kind, "name": p1_name},
                                "p2": {"kind": p2_kind, "name": p2_name},
                            }
                        },
                        f,
                    )
                with open(os.path.join(mdir, "result.json"), "w", encoding="utf-8") as f:
                    json.dump({"winner": winner}, f)
                result_paths.append(os.path.join(mdir, "result.json"))

            # Match 1: script-a beats script-b (with 1 round of stats)
            write_match(1, winner=1, p1_kind="script", p1_name="a", p2_kind="script", p2_name="b")
            # add per-round stats to match 1
            m1_dir = os.path.join(td, "m1")
            with open(os.path.join(m1_dir, "result.json"), "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "winner": 1,
                        "rounds": [
                            {
                                "round": 1,
                                "winner": 1,
                                "ticks": 10,
                                "end_reason": "ko",
                                "stats": {"p1_damage": 7, "p2_damage": 3, "p1_hits": 1, "p2_hits": 2, "avg_distance": 50.0},
                            }
                        ],
                    },
                    f,
                )

            # Match 2: script-b beats script-a (no stats)
            write_match(2, winner=2, p1_kind="script", p1_name="a", p2_kind="script", p2_name="b")
            # Match 3: tie (no stats)
            write_match(3, winner=None, p1_kind="script", p1_name="a", p2_kind="script", p2_name="b")

            board = aggregate_results(result_paths)
            self.assertEqual(board["schema"], "openclaw-battle.tournament.leaderboard.v2")
            self.assertEqual(board["matches"], 3)
            self.assertEqual(board["players"]["script-a"]["wins"], 1)
            self.assertEqual(board["players"]["script-a"]["losses"], 1)
            self.assertEqual(board["players"]["script-a"]["ties"], 1)
            self.assertEqual(board["players"]["script-b"]["wins"], 1)
            self.assertEqual(board["players"]["script-b"]["losses"], 1)
            self.assertEqual(board["players"]["script-b"]["ties"], 1)

            # Stats should be present (non-null) since match 1 included round stats
            self.assertEqual(
                board["players"]["script-a"]["stats"],
                {
                    "rounds": 1,
                    "damage_dealt": 7,
                    "damage_taken": 3,
                    "hits": 1,
                    "hits_taken": 2,
                    "avg_distance": 50.0,
                },
            )
            self.assertEqual(
                board["players"]["script-b"]["stats"],
                {
                    "rounds": 1,
                    "damage_dealt": 3,
                    "damage_taken": 7,
                    "hits": 2,
                    "hits_taken": 1,
                    "avg_distance": 50.0,
                },
            )


if __name__ == "__main__":
    unittest.main()
