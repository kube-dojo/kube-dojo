from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.calibration import constants
from scripts.calibration import report, schema
from scripts.calibration.models import model_by_canonical


def _score_row(
    *,
    scorer="deterministic",
    gate_name="gate",
    gate_pass=True,
    score_value=1.0,
):
    return SimpleNamespace(
        scorer=scorer,
        gate_name=gate_name,
        gate_pass=gate_pass,
        score_value=score_value,
    )


def _insert_cell(db_path, lane, fixture_id, canonical, score):
    model = model_by_canonical(canonical)
    row = schema.build_cell_row(
        lane=lane,
        fixture_id=fixture_id,
        model=model,
        run_date="2026-05-21",
    )
    with schema.connect(db_path) as conn:
        cell_id = schema.insert_cell(conn, row)
        schema.insert_dispatch(
            conn,
            cell_id=cell_id,
            task_id=f"task-{canonical}-{lane}",
            response_path=f"calibration/v1/2026-05-21/responses/{cell_id}.md",
            cost_usd=0.02,
        )
        schema.insert_score(
            conn,
            cell_id=cell_id,
            gate_name="gate",
            gate_pass=score == 1.0,
            score_value=score,
        )
    return cell_id


class TestComposite:
    def test_mechanical_lane_all_pass_is_a(self):
        composite, letter, _color = report.composite_score(
            [_score_row(gate_pass=True, score_value=None)],
            "code-writing",
        )

        assert composite == 10.0
        assert letter == "A"

    def test_mechanical_lane_half_pass_is_d(self):
        composite, letter, _color = report.composite_score(
            [
                _score_row(gate_pass=True, score_value=None),
                _score_row(gate_name="lint", gate_pass=False, score_value=None),
            ],
            "code-writing",
        )

        assert composite == 5.0
        assert letter == "D"

    def test_mechanical_lane_no_pass_is_f(self):
        composite, letter, _color = report.composite_score(
            [_score_row(gate_pass=False, score_value=None)],
            "code-review",
        )

        assert composite == 0.0
        assert letter == "F"

    def test_prose_lane_blends_gates_and_judges(self):
        composite, letter, _color = report.composite_score(
            [
                _score_row(gate_pass=True, score_value=1.0),
                _score_row(
                    scorer="llm-judge:one",
                    gate_name="llm_judge_score",
                    gate_pass=True,
                    score_value=9.5,
                ),
                _score_row(
                    scorer="llm-judge:two",
                    gate_name="llm_judge_score",
                    gate_pass=True,
                    score_value=9.0,
                ),
            ],
            "architecting",
        )

        assert composite == pytest.approx(9.55)
        assert letter == "A"

    def test_prose_lane_half_gates_and_mid_judges_is_d(self):
        composite, letter, _color = report.composite_score(
            [
                _score_row(gate_pass=True, score_value=None),
                _score_row(gate_name="lint", gate_pass=False, score_value=None),
                _score_row(
                    scorer="llm-judge:one",
                    gate_name="judge_one",
                    gate_pass=True,
                    score_value=5.0,
                ),
                _score_row(
                    scorer="llm-judge:two",
                    gate_name="judge_two",
                    gate_pass=True,
                    score_value=5.0,
                ),
            ],
            "content-writing-long",
        )

        assert composite == 5.0
        assert letter == "D"

    def test_prose_lane_unparseable_judges_is_gate_weight_penalized(self):
        composite, letter, _color = report.composite_score(
            [
                _score_row(gate_pass=True, score_value=0.8),
                _score_row(
                    scorer="llm-judge:one",
                    gate_name="judge_one",
                    gate_pass=False,
                    score_value=None,
                ),
                _score_row(
                    scorer="llm-judge:two",
                    gate_name="judge_two",
                    gate_pass=False,
                    score_value=None,
                ),
            ],
            "summarization",
        )

        assert composite == pytest.approx(3.2)
        assert letter == "F"

    def test_judge_dissent_uses_mean_and_flags(self):
        rows = [
            _score_row(gate_pass=True, score_value=1.0),
            _score_row(
                scorer="llm-judge:one",
                gate_name="judge_one",
                gate_pass=True,
                score_value=9.0,
            ),
            _score_row(
                scorer="llm-judge:two",
                gate_name="judge_two",
                gate_pass=True,
                score_value=6.5,
            ),
        ]

        composite, letter, _color = report.composite_score(rows, "architecting")

        assert composite == pytest.approx(8.65)
        assert letter == "A"
        assert report.judge_dissent(rows, "architecting") is True

    def test_composite_clamps_to_ten(self):
        composite, letter, _color = report.composite_score(
            [
                _score_row(gate_pass=True, score_value=1.0),
                _score_row(
                    scorer="llm-judge:one",
                    gate_name="judge_one",
                    gate_pass=True,
                    score_value=20.0,
                ),
            ],
            "architecting",
        )

        assert composite == 10.0
        assert letter == "A"

    def test_report_reads_constants_for_weights_and_grades(self, monkeypatch):
        monkeypatch.setattr(constants, "COMPOSITE_GATE_WEIGHT", 1.0)
        monkeypatch.setattr(constants, "COMPOSITE_JUDGE_WEIGHT", 0.0)
        monkeypatch.setattr(
            constants,
            "LETTER_GRADE_BANDS",
            [("Z", 0.0, 10.01, "#000000")],
        )

        composite, letter, color = report.composite_score(
            [
                _score_row(gate_pass=True, score_value=None),
                _score_row(gate_name="lint", gate_pass=False, score_value=None),
                _score_row(
                    scorer="llm-judge:one",
                    gate_name="judge_one",
                    gate_pass=True,
                    score_value=10.0,
                ),
            ],
            "content-writing-long",
        )

        assert composite == 5.0
        assert letter == "Z"
        assert color == "#000000"


def test_report_renders_matrix_per_lane_and_per_model(tmp_path):
    db_path = tmp_path / "ledger.db"
    schema.init_db(db_path)
    cell_id = _insert_cell(
        db_path,
        "code-writing",
        "parse-dependabot-cooldown",
        "gpt-5.5",
        1.0,
    )
    _insert_cell(db_path, "code-writing", "parse-dependabot-cooldown", "claude-opus-4-7", 0.0)
    _insert_cell(db_path, "fact-check", "k8s-1-35-claims", "gpt-5.5", 1.0)
    _insert_cell(db_path, "fact-check", "k8s-1-35-claims", "claude-opus-4-7", 1.0)
    with schema.connect(db_path) as conn:
        schema.insert_score(
            conn,
            cell_id=cell_id,
            gate_name="llm_judge_score",
            gate_pass=False,
            score_value=None,
            scorer="llm-judge:dummy",
            gate_failure_reason="scorer_unparseable_output",
        )

    out_dir = tmp_path / "reports"
    written = report.render_reports(db_path=db_path, out_dir=out_dir)

    matrix = (out_dir / "matrix.html").read_text(encoding="utf-8")
    per_lane = (out_dir / "per-lane" / "code-writing.html").read_text(
        encoding="utf-8",
    )
    per_model = (out_dir / "per-model" / "gpt-5.5.html").read_text(
        encoding="utf-8",
    )
    index = (out_dir / "index.html").read_text(encoding="utf-8")

    assert out_dir / "matrix.html" in written
    assert cell_id in matrix
    assert "code-writing" in matrix
    assert 'class="grade-pill"' in matrix
    assert "10.0" in matrix
    assert ">A<" in matrix
    assert "gates=100% · judges=[n/a]" in matrix
    assert "Σ" in matrix
    assert "gpt-5.5" in per_lane
    assert "bar-fill" in per_lane
    assert "★" in per_lane
    assert "<svg" in per_model
    assert "Strengths" in per_model
    assert "effort signal" in per_model.lower()
    assert "$0.0800" in index
