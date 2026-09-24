from eb1.qa import needs_category, evidence_context, normalized


def test_category_clarification_and_comparison():
    assert needs_category('Do I need a job offer?', 'Both')
    assert not needs_category('Do I need a job offer?', 'EB-1A')
    assert not needs_category('Compare the job offer requirements in both categories.', 'Both')
    assert not needs_category('What is the EB-1B judging criterion?', 'Both')


def test_evidence_spans_are_exact_substrings():
    passage = {'id': 'test', 'document_id': 'eb1a', 'section': 'Evidence',
               'text': 'This is the first exact source sentence.\n\nThis is another exact source sentence.'}
    context, catalog = evidence_context([passage])
    assert len(catalog) == 2
    for span in catalog.values():
        assert normalized(span['text']) in normalized(passage['text'])
