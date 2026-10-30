from app.harness import answer_question, summarize_deck
from app.models import Answer, Claim
from tests.conftest import GOOD_SUMMARY, HALLUCINATED_SUMMARY, FakeJudge, FakeLLM


def test_passes_first_try(sorting_deck):
    llm = FakeLLM(summaries=[GOOD_SUMMARY])
    result = summarize_deck(sorting_deck, llm)
    assert result.report.passed and result.attempts == 1


def test_failed_claims_are_fed_back_and_revised(sorting_deck):
    llm = FakeLLM(summaries=[HALLUCINATED_SUMMARY, GOOD_SUMMARY])
    result = summarize_deck(sorting_deck, llm)
    assert result.attempts == 2 and result.report.passed
    assert llm.feedback_seen[0] == []  # first call: no feedback
    assert len(llm.feedback_seen[1]) == 2  # second call: both failures sent back
    assert len(result.trace) == 2


def test_out_of_retries_drops_unverified_claims(sorting_deck):
    llm = FakeLLM(summaries=[HALLUCINATED_SUMMARY] * 3)
    result = summarize_deck(sorting_deck, llm, max_revisions=2)
    assert result.attempts == 3
    assert [c.text for c in result.output.abstract] == ["Merge sort runs in O(n log n) time."]


def test_answer_maps_context_citations_back_to_real_slides(sorting_deck):
    # Retrieval ranks the quick sort slide first, so the model cites context slide 1
    llm = FakeLLM(answers=[Answer(claims=[Claim(text="Worst case is O(n^2).", slides=[1])])])
    result, cites = answer_question("quick sort worst case pivot", [sorting_deck], llm)
    assert result.report.passed
    assert cites[1].slide == 3 and cites[1].deck_id == "d1"


def test_answer_with_no_matching_slides_says_so(sorting_deck):
    result, cites = answer_question("photosynthesis chlorophyll", [sorting_deck], FakeLLM())
    assert result.output.insufficient_evidence and cites == {}


def test_answer_hallucination_is_removed(sorting_deck):
    bad = Answer(claims=[Claim(text="Quick sort is always faster.", slides=[1])])
    llm = FakeLLM(answers=[bad, bad])
    result, _ = answer_question("quick sort", [sorting_deck], llm, judge=FakeJudge("always faster"))
    assert result.output.claims == [] and result.output.insufficient_evidence
