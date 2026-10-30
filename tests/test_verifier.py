from app.models import Claim
from app.verifier import check_claim, extract_facts, verify_summary
from tests.conftest import GOOD_SUMMARY, HALLUCINATED_SUMMARY, FakeJudge


def test_grounded_summary_passes(sorting_deck):
    report = verify_summary(GOOD_SUMMARY, sorting_deck)
    assert report.passed, report.issues
    assert report.claims_supported == report.claims_total == 3


def test_catches_wrong_number_and_fake_slide(sorting_deck):
    report = verify_summary(HALLUCINATED_SUMMARY, sorting_deck)
    checks = {i.check for i in report.issues}
    assert not report.passed
    assert checks == {"exact_fact", "citation"}
    assert report.claims_supported == 1


def test_number_must_be_on_the_cited_slide_not_just_anywhere(sorting_deck):
    # 0.42 is real, but it's on slide 4, not slide 2
    issues = check_claim(Claim(text="Merge sort took 0.42 seconds.", slides=[2]), sorting_deck)
    assert issues and issues[0].check == "exact_fact"


def test_code_identifiers_must_match(sorting_deck):
    ok = check_claim(Claim(text="Halves are combined with `merge()`.", slides=[2]), sorting_deck)
    bad = check_claim(Claim(text="Halves are combined with `combine()`.", slides=[2]), sorting_deck)
    assert ok == [] and bad[0].check == "exact_fact"


def test_number_formatting_is_normalized(sorting_deck):
    claim = Claim(text="It sorted 1000000 integers.", slides=[4])  # slide says 1,000,000
    assert check_claim(claim, sorting_deck) == []


def test_judge_catches_unsupported_paraphrase(sorting_deck):
    claim = Claim(text="Quick sort is always faster than merge sort.", slides=[3])
    assert check_claim(claim, sorting_deck) == []  # no facts to string-match
    issues = check_claim(claim, sorting_deck, FakeJudge("always faster"))
    assert issues[0].check == "judge"


def test_extract_facts():
    assert extract_facts('Load factor 0.75 and "chaining" via `put()`') == ["0.75", "chaining", "put()"]
