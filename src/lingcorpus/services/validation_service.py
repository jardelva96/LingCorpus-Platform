"""Serviço de validação de dados textuais."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ValidationIssue:
    """Um problema encontrado na validação."""

    level: str  # "error", "warning", "info"
    message: str
    line: int | None = None


@dataclass
class ValidationReport:
    """Relatório completo de validação de um documento."""

    filename: str
    is_valid: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)
    encoding_ok: bool = True
    has_content: bool = True
    line_count: int = 0
    blank_line_ratio: float = 0.0


def validate_text_content(text: str, filename: str = "") -> ValidationReport:
    """Valida o conteúdo de um documento textual.

    Verificações:
    - Conteúdo não vazio
    - Codificação válida (caracteres de substituição)
    - Proporção de linhas em branco
    - Linhas muito longas
    - Caracteres de controle
    - Consistência de quebra de linha
    """
    report = ValidationReport(filename=filename)
    issues = []

    # Verifica conteúdo vazio
    if not text or not text.strip():
        report.is_valid = False
        report.has_content = False
        issues.append(ValidationIssue("error", "Documento vazio ou contém apenas espaços"))
        report.issues = issues
        return report

    lines = text.splitlines()
    report.line_count = len(lines)

    # Verifica caracteres de substituição (codificação ruim)
    replacement_count = text.count("\ufffd")
    if replacement_count > 0:
        ratio = replacement_count / len(text)
        if ratio > 0.01:
            report.encoding_ok = False
            issues.append(ValidationIssue(
                "error",
                f"Codificação suspeita: {replacement_count} caracteres de substituição "
                f"({ratio:.1%} do texto)",
            ))
        else:
            issues.append(ValidationIssue(
                "warning",
                f"{replacement_count} caracteres de substituição encontrados",
            ))

    # Verifica linhas em branco
    blank_lines = sum(1 for line in lines if not line.strip())
    report.blank_line_ratio = blank_lines / len(lines) if lines else 0.0
    if report.blank_line_ratio > 0.5:
        issues.append(ValidationIssue(
            "warning",
            f"Alta proporção de linhas em branco: {report.blank_line_ratio:.1%}",
        ))

    # Verifica linhas muito longas
    long_lines = [(i + 1, len(line)) for i, line in enumerate(lines) if len(line) > 10000]
    for line_num, length in long_lines[:5]:
        issues.append(ValidationIssue(
            "warning",
            f"Linha {line_num} muito longa ({length} caracteres)",
            line=line_num,
        ))

    # Verifica caracteres de controle (exceto \n, \r, \t)
    control_chars = re.findall(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text)
    if control_chars:
        issues.append(ValidationIssue(
            "warning",
            f"{len(control_chars)} caracteres de controle encontrados",
        ))

    # Verifica consistência de quebra de linha
    crlf = text.count("\r\n")
    lf_only = text.count("\n") - crlf
    if crlf > 0 and lf_only > 0:
        issues.append(ValidationIssue(
            "info",
            f"Quebras de linha mistas: {crlf} CRLF e {lf_only} LF",
        ))

    # Determina validade
    report.is_valid = not any(i.level == "error" for i in issues)
    report.issues = issues
    return report


def validate_csv_content(text: str, filename: str = "", delimiter: str = ",") -> ValidationReport:
    """Valida o conteúdo de um arquivo CSV."""
    base_report = validate_text_content(text, filename)
    if not base_report.has_content:
        return base_report

    lines = text.splitlines()
    issues = list(base_report.issues)

    # Verifica consistência de colunas
    col_counts = [len(line.split(delimiter)) for line in lines if line.strip()]
    if col_counts:
        expected = col_counts[0]
        inconsistent = [
            (i + 1, count)
            for i, count in enumerate(col_counts)
            if count != expected
        ]
        if inconsistent:
            issues.append(ValidationIssue(
                "warning",
                f"{len(inconsistent)} linhas com número inconsistente de colunas "
                f"(esperado: {expected})",
            ))
            for line_num, count in inconsistent[:3]:
                issues.append(ValidationIssue(
                    "info",
                    f"Linha {line_num}: {count} colunas (esperado: {expected})",
                    line=line_num,
                ))

    base_report.issues = issues
    base_report.is_valid = not any(i.level == "error" for i in issues)
    return base_report
