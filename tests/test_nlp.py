"""Testes do serviço de NLP."""

from __future__ import annotations

from lingcorpus.services.nlp_service import (
    compute_frequencies,
    compute_statistics,
    concordance,
    ngrams,
    tokenize,
)

SAMPLE_PT = (
    "A linguística computacional é uma área interdisciplinar que combina "
    "técnicas de ciência da computação com a linguística. A área tem crescido "
    "muito nos últimos anos com o avanço do processamento de língua natural."
)

SAMPLE_EN = (
    "Computational linguistics is an interdisciplinary field that combines "
    "computer science techniques with linguistics. The field has grown "
    "significantly in recent years with advances in natural language processing."
)


def test_tokenize_pt():
    """Tokeniza texto em português."""
    tokens = tokenize(SAMPLE_PT, "pt")
    assert len(tokens) > 10
    assert "linguística" in tokens or "linguistica" in [t.lower() for t in tokens]


def test_tokenize_en():
    """Tokeniza texto em inglês."""
    tokens = tokenize(SAMPLE_EN, "en")
    assert len(tokens) > 10
    assert "linguistics" in [t.lower() for t in tokens]


def test_compute_statistics():
    """Calcula estatísticas descritivas do texto."""
    stats = compute_statistics(SAMPLE_PT, "pt")
    assert stats.total_tokens > 0
    assert stats.total_types > 0
    assert 0 < stats.type_token_ratio <= 1.0
    assert stats.avg_word_length > 0
    assert stats.hapax_legomena >= 0


def test_compute_statistics_empty():
    """Retorna estatísticas zeradas para texto vazio."""
    stats = compute_statistics("", "pt")
    assert stats.total_tokens == 0
    assert stats.total_types == 0


def test_compute_frequencies():
    """Calcula frequência de palavras com remoção de stopwords."""
    tokens = tokenize(SAMPLE_PT, "pt")
    freqs = compute_frequencies(tokens, remove_stopwords=True, language="pt")
    assert len(freqs) > 0
    # Stopwords devem ter sido removidas
    freq_words = [w for w, _ in freqs]
    assert "de" not in freq_words
    assert "a" not in freq_words


def test_compute_frequencies_no_stopwords():
    """Calcula frequência sem remover stopwords."""
    tokens = tokenize(SAMPLE_PT, "pt")
    freqs_with = compute_frequencies(tokens, remove_stopwords=False, language="pt")
    freqs_without = compute_frequencies(tokens, remove_stopwords=True, language="pt")
    assert len(freqs_with) > len(freqs_without)


def test_concordance():
    """Gera linhas de concordância KWIC."""
    results = concordance(SAMPLE_PT, "linguística", window=3, language="pt")
    assert len(results) > 0
    assert results[0].keyword.lower() == "linguística"
    assert results[0].left_context != ""


def test_concordance_not_found():
    """Retorna lista vazia para palavra inexistente."""
    results = concordance(SAMPLE_PT, "inexistente", language="pt")
    assert len(results) == 0


def test_ngrams():
    """Calcula bigramas mais frequentes."""
    tokens = tokenize(SAMPLE_PT, "pt")
    bigrams = ngrams(tokens, n=2)
    assert len(bigrams) > 0
    # Cada bigrama deve conter dois tokens separados por espaço
    gram, freq = bigrams[0]
    assert " " in gram
    assert freq >= 1


def test_trigrams():
    """Calcula trigramas."""
    tokens = tokenize(SAMPLE_PT, "pt")
    trigrams = ngrams(tokens, n=3)
    assert len(trigrams) > 0
    gram, _ = trigrams[0]
    assert gram.count(" ") == 2
