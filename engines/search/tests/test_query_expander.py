import pytest
from engines.search.discovery.query_expander import QueryExpander

def test_query_expander_normalization():
    expander = QueryExpander()
    assert expander._normalize("  Dewa   19  ") == "Dewa 19"
    assert expander._normalize("\tColdplay\n") == "Coldplay"

def test_query_expander_expand():
    expander = QueryExpander()
    results = expander.expand("Dewa 19", count=3)
    
    assert len(results) == 3
    assert results[0] == "Dewa 19 full album timestamp"
    assert results[1] == "Dewa 19 greatest hits timestamp"
    assert results[2] == "Dewa 19 best songs timestamp"

def test_query_expander_expand_count():
    expander = QueryExpander()
    results = expander.expand("Noah", count=10) # Ask for more than available
    
    assert len(results) == 7 # Only 7 templates available
    assert results[-1] == "Noah full album"
