from __future__ import annotations

import json
import os
import tempfile

from artifacts import begin_match, RoundResult


def test_begin_match_writes_meta_and_optional_events():
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
        assert os.path.exists(meta_path)
        meta = json.load(open(meta_path, "r", encoding="utf-8"))
        assert meta["schema"] == "openclaw-battle.artifacts.meta.v0"
        assert meta["mode"] == "MATCH"
        assert meta["best_of"] == 3
        assert meta["fixed_tick_match"] is True
        assert meta["fps"] == 60
        assert "match_id" in meta

        # events
        assert ma.events_path is not None
        assert os.path.exists(ma.events_path)


def test_finalize_writes_result_schema_and_rounds():
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

        # two rounds: p1 wins 2-0
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
        # Round 2 has no stats; the writer should omit the stats object entirely.
        ma.add_round(RoundResult(round=2, winner=1, ticks=120, end_reason="timeout"))
        ma.finalize()

        res_path = os.path.join(ma.out_dir, "result.json")
        assert os.path.exists(res_path)
        res = json.load(open(res_path, "r", encoding="utf-8"))
        assert res["schema"] == "openclaw-battle.artifacts.result.v0"
        assert res["winner"] == 1
        assert res["score"]["p1"] == 2
        assert res["score"]["p2"] == 0
        assert len(res["rounds"]) == 2
        assert res["rounds"][0]["round"] == 1
        assert res["rounds"][0]["ticks"] == 100
        assert res["rounds"][0]["stats"] == {
            "p1_damage": 25,
            "p2_damage": 10,
            "p1_hits": 3,
            "p2_hits": 1,
            "avg_distance": 123.5,
        }
        assert res["rounds"][1]["stats"] is None
