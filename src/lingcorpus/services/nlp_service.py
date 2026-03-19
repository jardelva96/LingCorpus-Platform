"""Serviço de Processamento de Língua Natural para análise de corpus."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

from lingcorpus.config import settings

# Configura diretório NLTK
nltk.data.path.insert(0, str(settings.nltk_data_dir))

_PUNKT_READY = False


def _ensure_punkt() -> None:
    """Baixa o tokenizador punkt se necessário."""
    global _PUNKT_READY  # noqa: PLW0603
    if _PUNKT_READY:
        return
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", download_dir=str(settings.nltk_data_dir), quiet=True)
    _PUNKT_READY = True


_STOPWORDS_PT = {
    "a", "o", "e", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "um", "uma", "uns", "umas", "por", "para", "com", "sem", "que", "se", "ao", "aos",
    "à", "às", "ou", "é", "são", "foi", "ser", "ter", "como", "mais", "não", "muito",
    "já", "também", "só", "seu", "sua", "seus", "suas", "ele", "ela", "eles", "elas",
    "me", "te", "lhe", "vos", "lhes", "este", "esta", "esse", "essa", "isto",
    "isso", "aquele", "aquela", "aquilo", "entre", "sobre", "até", "após", "desde",
    "durante", "ainda", "quando", "onde", "porque", "mas", "porém", "contudo", "nem",
    "eu", "tu", "nós", "vós", "meu", "minha", "teu", "tua", "nosso", "nossa",
}

_STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "is", "was", "are", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "can", "shall", "not", "no", "nor", "so", "if", "then", "than", "too", "very",
    "just", "about", "above", "after", "again", "all", "also", "any", "as", "because",
    "before", "between", "both", "each", "few", "her", "here", "him", "his", "how",
    "i", "it", "its", "me", "more", "most", "my", "now", "only", "other", "our",
    "out", "own", "same", "she", "some", "such", "that", "their", "them", "there",
    "these", "they", "this", "those", "through", "up", "we", "what", "when", "where",
    "which", "while", "who", "whom", "why", "you", "your",
}

STOPWORDS = {"pt": _STOPWORDS_PT, "en": _STOPWORDS_EN}


def normalize_token(token: str) -> str:
    """Normaliza um token: lowercase e remoção de acentos opcionais."""
    return token.lower().strip()


def is_word(token: str) -> bool:
    """Verifica se o token é uma palavra (não pontuação)."""
    return bool(re.match(r"^[\w]+$", token, re.UNICODE))


@dataclass
class TextStats:
    """Estatísticas descritivas de um texto."""

    total_tokens: int = 0
    total_types: int = 0
    type_token_ratio: float = 0.0
    avg_word_length: float = 0.0
    avg_sentence_length: float = 0.0
    hapax_legomena: int = 0
    hapax_ratio: float = 0.0


@dataclass
class ConcordanceResult:
    """Uma linha de concordância KWIC (Key Word In Context)."""

    left_context: str
    keyword: str
    right_context: str
    document: str = ""


def tokenize(text: str, language: str = "pt") -> list[str]:
    """Tokeniza texto usando NLTK com fallback para regex."""
    _ensure_punkt()
    lang_map = {"pt": "portuguese", "en": "english", "es": "spanish"}
    try:
        tokens = word_tokenize(text, language=lang_map.get(language, "portuguese"))
    except LookupError:
        tokens = re.findall(r"\b\w+\b", text, re.UNICODE)
    return tokens


def sentence_split(text: str, language: str = "pt") -> list[str]:
    """Divide texto em sentenças."""
    _ensure_punkt()
    lang_map = {"pt": "portuguese", "en": "english", "es": "spanish"}
    try:
        return sent_tokenize(text, language=lang_map.get(language, "portuguese"))
    except LookupError:
        return re.split(r"[.!?]+", text)


def compute_frequencies(
    tokens: list[str],
    remove_stopwords: bool = True,
    language: str = "pt",
) -> list[tuple[str, int]]:
    """Calcula frequência de tokens, opcionalmente removendo stopwords."""
    stopwords = STOPWORDS.get(language, _STOPWORDS_PT) if remove_stopwords else set()
    words = [normalize_token(t) for t in tokens if is_word(t)]
    filtered = [w for w in words if w and w not in stopwords and len(w) > 1]
    return Counter(filtered).most_common()


def compute_statistics(text: str, language: str = "pt") -> TextStats:
    """Calcula estatísticas descritivas completas do texto."""
    tokens = tokenize(text, language)
    words = [normalize_token(t) for t in tokens if is_word(t)]
    sentences = sentence_split(text, language)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not words:
        return TextStats()

    freq = Counter(words)
    total_tokens = len(words)
    total_types = len(freq)
    hapax = sum(1 for count in freq.values() if count == 1)

    return TextStats(
        total_tokens=total_tokens,
        total_types=total_types,
        type_token_ratio=total_types / total_tokens if total_tokens else 0.0,
        avg_word_length=sum(len(w) for w in words) / total_tokens,
        avg_sentence_length=total_tokens / len(sentences) if sentences else 0.0,
        hapax_legomena=hapax,
        hapax_ratio=hapax / total_tokens if total_tokens else 0.0,
    )


def concordance(
    text: str,
    keyword: str,
    window: int = 5,
    language: str = "pt",
    document_name: str = "",
) -> list[ConcordanceResult]:
    """Gera linhas de concordância KWIC para uma palavra-chave."""
    tokens = tokenize(text, language)
    normalized = [normalize_token(t) for t in tokens]
    keyword_lower = keyword.lower().strip()

    results = []
    for i, token in enumerate(normalized):
        if token == keyword_lower:
            left = " ".join(tokens[max(0, i - window) : i])
            right = " ".join(tokens[i + 1 : i + 1 + window])
            results.append(ConcordanceResult(
                left_context=left,
                keyword=tokens[i],
                right_context=right,
                document=document_name,
            ))
    return results


def ngrams(tokens: list[str], n: int = 2) -> list[tuple[str, int]]:
    """Calcula n-gramas mais frequentes."""
    words = [normalize_token(t) for t in tokens if is_word(t)]
    grams = [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]
    return Counter(grams).most_common()
