"""Testes do serviço de validação de dados."""

from __future__ import annotations

from lingcorpus.services.validation_service import (
    validate_csv_content,
    validate_text_content,
)


def test_validate_empty_text():
    """Rejeita texto vazio."""
    report = validate_text_content("")
    assert not report.is_valid
    assert not report.has_content


def test_validate_normal_text():
    """Aceita texto normal."""
    text = "Este é um texto normal para teste de validação."
    report = validate_text_content(text, "test.txt")
    assert report.is_valid
    assert report.has_content
    assert report.filename == "test.txt"


def test_validate_replacement_chars():
    """Detecta caracteres de substituição (codificação ruim)."""
    text = "Texto com muitos \ufffd\ufffd\ufffd\ufffd caracteres \ufffd inválidos"
    report = validate_text_content(text)
    assert any("substituição" in i.message for i in report.issues)


def test_validate_high_blank_ratio():
    """Alerta sobre proporção alta de linhas em branco."""
    text = "Linha 1\n\n\n\n\n\n\n\n\n\nLinha 2"
    report = validate_text_content(text)
    assert report.blank_line_ratio > 0.5
    assert any("branco" in i.message.lower() for i in report.issues)


def test_validate_control_chars():
    """Detecta caracteres de controle."""
    text = "Texto com caractere \x00 de controle \x01"
    report = validate_text_content(text)
    assert any("controle" in i.message for i in report.issues)


def test_validate_mixed_line_endings():
    """Detecta quebras de linha mistas."""
    text = "Linha CRLF\r\nLinha LF\nOutra CRLF\r\n"
    report = validate_text_content(text)
    assert any("mistas" in i.message.lower() for i in report.issues)


def test_validate_csv_consistent():
    """Valida CSV com colunas consistentes."""
    csv = "col1,col2,col3\na,b,c\nd,e,f"
    report = validate_csv_content(csv, "test.csv")
    assert report.is_valid


def test_validate_csv_inconsistent():
    """Detecta CSV com número inconsistente de colunas."""
    csv = "col1,col2,col3\na,b\nc,d,e,f"
    report = validate_csv_content(csv, "test.csv")
    assert any("inconsistente" in i.message for i in report.issues)


def test_validate_long_lines():
    """Detecta linhas muito longas."""
    text = "Linha normal\n" + "x" * 15000 + "\nOutra linha"
    report = validate_text_content(text)
    assert any("longa" in i.message.lower() for i in report.issues)
