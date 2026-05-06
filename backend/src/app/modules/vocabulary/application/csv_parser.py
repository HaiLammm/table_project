import csv
import io
import re
from dataclasses import dataclass, field
from typing import Literal

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

ColumnMapping = {
    "term": "term",
    "word": "term",
    "vocabulary": "term",
    "language": "language",
    "lang": "language",
    "definition": "definition",
    "meaning": "definition",
    "tags": "tags",
    "category": "tags",
    "cefr": "cefr_level",
    "cefr_level": "cefr_level",
    "jlpt": "jlpt_level",
    "jlpt_level": "jlpt_level",
    "part_of_speech": "part_of_speech",
    "pos": "part_of_speech",
}


@dataclass
class ParsedCSVRow:
    term: str | None = None
    language: str | None = None
    definition: str | None = None
    cefr_level: str | None = None
    jlpt_level: str | None = None
    part_of_speech: str | None = None
    tags: list[str] = field(default_factory=list)
    parent_chain: list[str] = field(default_factory=list)
    row_number: int = 0
    status: Literal["valid", "warning", "error"] = "valid"
    error_message: str | None = None


@dataclass
class ParseResult:
    rows: list[ParsedCSVRow]
    total_rows: int
    valid_count: int
    warning_count: int
    error_count: int
    detected_columns: list[str]


def _normalize_header(header: str) -> str:
    return header.strip().lower()


def _map_column_to_field(column: str) -> str | None:
    return ColumnMapping.get(_normalize_header(column))


def _detect_encoding_and_delimiter(content: bytes) -> tuple[str, str]:
    text = content.decode("utf-8-sig")
    if "\t" in text[:2048]:
        delimiter = "\t"
    else:
        try:
            dialect = csv.Sniffer().sniff(text[:2048], delimiters=",\t")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","
    return text, delimiter


def _detect_columns(headers: list[str]) -> list[str]:
    detected = []
    for header in headers:
        field = _map_column_to_field(header)
        if field:
            detected.append(field)
    return detected


def parse_csv(file_content: bytes) -> ParseResult:
    text, delimiter = _detect_encoding_and_delimiter(file_content)

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = reader.fieldnames or []

    detected_columns = _detect_columns(headers)
    rows: list[ParsedCSVRow] = []
    valid_count = 0
    warning_count = 0
    error_count = 0

    for row_number, row in enumerate(reader, start=1):
        parsed = _parse_row(row, row_number)
        rows.append(parsed)

        if parsed.status == "valid":
            valid_count += 1
        elif parsed.status == "warning":
            warning_count += 1
        else:
            error_count += 1

    return ParseResult(
        rows=rows,
        total_rows=len(rows),
        valid_count=valid_count,
        warning_count=warning_count,
        error_count=error_count,
        detected_columns=detected_columns,
    )


def _parse_row(row: dict[str, str], row_number: int) -> ParsedCSVRow:
    parsed = ParsedCSVRow(row_number=row_number)

    for col_name, col_value in row.items():
        if col_value is None:
            continue

        field = _map_column_to_field(col_name)
        if field is None:
            continue

        col_value = col_value.strip()

        if field == "term":
            if not col_value:
                parsed.status = "error"
                parsed.error_message = "Missing required field: term"
                return parsed
            if len(col_value) > 100:
                parsed.status = "error"
                parsed.error_message = f"Term exceeds maximum length of 100 characters"
                return parsed
            if HTML_TAG_PATTERN.search(col_value):
                parsed.status = "warning"
                parsed.error_message = "Term contains HTML tags"
            parsed.term = col_value

        elif field == "language":
            if col_value not in ("en", "jp", None, ""):
                parsed.status = "warning"
                parsed.error_message = f"Unknown language '{col_value}', defaulting to 'en'"
                parsed.language = "en"
            else:
                parsed.language = col_value if col_value else "en"

        elif field == "definition":
            parsed.definition = col_value if col_value else None

        elif field == "cefr_level":
            valid_levels = {"A1", "A2", "B1", "B2", "C1", "C2"}
            if col_value and col_value.upper() in valid_levels:
                parsed.cefr_level = col_value.upper()
            elif col_value:
                parsed.status = "warning"
                parsed.error_message = f"Invalid CEFR level '{col_value}'"

        elif field == "jlpt_level":
            valid_levels = {"N1", "N2", "N3", "N4", "N5"}
            if col_value and col_value.upper() in valid_levels:
                parsed.jlpt_level = col_value.upper()
            elif col_value:
                parsed.status = "warning"
                parsed.error_message = f"Invalid JLPT level '{col_value}'"

        elif field == "part_of_speech":
            parsed.part_of_speech = col_value if col_value else None

        elif field == "tags":
            if col_value:
                tags = [t.strip() for t in col_value.split("::")]
                for tag in tags:
                    if "::" in tag:
                        parts = tag.split("::")
                        parsed.parent_chain.extend([p.strip() for p in parts if p.strip()])
                    else:
                        parsed.tags.append(tag)

    if parsed.term is None:
        parsed.status = "error"
        parsed.error_message = "Missing required field: term"

    if parsed.language is None:
        parsed.language = "en"

    return parsed


def rows_to_terms(rows: list[ParsedCSVRow]) -> list[dict]:
    terms = []
    for row in rows:
        if row.status != "valid":
            continue
        term_dict: dict = {
            "term": row.term,
            "language": row.language or "en",
        }
        if row.definition:
            term_dict["definition"] = row.definition
        if row.cefr_level:
            term_dict["cefr_level"] = row.cefr_level
        if row.jlpt_level:
            term_dict["jlpt_level"] = row.jlpt_level
        if row.part_of_speech:
            term_dict["part_of_speech"] = row.part_of_speech
        terms.append(term_dict)
    return terms
