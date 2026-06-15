"""Offline precision tests for scripts/quality/check_arxiv_citations.py (issue #1991).

These lock the `_title_like` classifier — the part that decides which arXiv link
texts are checkable paper titles vs prose/tags/citations. Keeping this strict is
what holds the false-positive rate at ~0 so the CI gate stays load-bearing. No
network is used (we never call fetch_title here).
"""
import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "check_arxiv_citations",
    Path(__file__).resolve().parents[1] / "scripts" / "quality" / "check_arxiv_citations.py",
)
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)


# --- link texts that ARE checkable titles (real paper titles) -> validated ---
CHECKABLE = [
    "Isolation Forest (Liu, Ting, Zhou 2008)",
    "A Survey on Concept Drift Adaptation",
    "Product Quantization for Nearest Neighbor Search",
    "Passage Re-ranking with BERT (NAACL 2019)",
    "Gama et al. — A Survey on Concept Drift Adaptation",      # author prefix stripped
    "D'Amour et al. — Underspecification in ML pipelines",
    "Attention Is All You Need",
    "The SPACE of Developer Productivity",
]

# --- link texts that are NOT titles -> skipped (cannot validate, must not flag) ---
SKIPPED = [
    "arxiv.org/abs/2309.06180",                                # bare url
    "https://arxiv.org/abs/2307.03172",                        # bare url
    "arXiv:2404.07143",                                        # bare arxiv ref
    "Kipf & Welling, 2017",                                    # author-year only
    "He et al., 2021",                                         # author-year only
    "SimCLR",                                                  # short tag
    "HNSW paper",                                              # short tag
    "MoCo",                                                    # short tag
    "Hypothetical Document Embeddings (HyDE)",                 # method name (acronym paren)
    "SHAP — Lundberg & Lee (2017)",                            # tag + author citation
    "In March 2022, OpenAI published the InstructGPT paper",   # prose sentence (verb)
    "every active sequence produces a key-value cache entry",  # lowercase prose phrase
    "the original paper",                                      # generic prose
]


def test_real_titles_are_checkable():
    for text in CHECKABLE:
        assert mod._title_like(text) is not None, f"should be checkable: {text!r}"


def test_non_titles_are_skipped():
    for text in SKIPPED:
        assert mod._title_like(text) is None, f"should be skipped: {text!r}"


def test_overlap_helper_flags_offdomain_only():
    # correct citation: claimed title overlaps the real title -> high overlap
    claimed = mod._norm_tokens("Isolation Forest")
    real = mod._norm_tokens("Isolation Forest")
    assert len(claimed & real) / len(claimed) >= 0.30
    # wrong id: claimed title vs an unrelated (math) paper -> ~0 overlap
    wrong = mod._norm_tokens("On polytopes associated to factorisations of prime-powers")
    assert len(claimed & wrong) / len(claimed) < 0.30


def test_arxiv_ok_whitelist_regex():
    assert mod.OK_RE.findall("text <!-- arxiv-ok: 2203.02155 --> more") == ["2203.02155"]


def test_link_regex_extracts_id_and_text():
    md = "see [Attention Is All You Need](https://arxiv.org/abs/1706.03762) for details"
    assert mod.LINK_RE.findall(md) == [("Attention Is All You Need", "1706.03762")]
