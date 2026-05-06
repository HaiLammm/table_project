import pytest

from src.app.modules.vocabulary.application.csv_parser import (
    _detect_encoding_and_delimiter,
    _map_column_to_field,
    _normalize_header,
    _parse_row,
    parse_csv,
)


class TestNormalizeHeader:
    def test_strips_whitespace(self):
        assert _normalize_header("  Term  ") == "term"

    def test_lowercase(self):
        assert _normalize_header("LANGUAGE") == "language"

    def test_mixed(self):
        assert _normalize_header("Definition ") == "definition"


class TestMapColumnToField:
    def test_term_variations(self):
        assert _map_column_to_field("term") == "term"
        assert _map_column_to_field("word") == "term"
        assert _map_column_to_field("vocabulary") == "term"

    def test_language_variations(self):
        assert _map_column_to_field("language") == "language"
        assert _map_column_to_field("lang") == "language"

    def test_definition_variations(self):
        assert _map_column_to_field("definition") == "definition"
        assert _map_column_to_field("meaning") == "definition"

    def test_tags_variations(self):
        assert _map_column_to_field("tags") == "tags"
        assert _map_column_to_field("category") == "tags"

    def test_cefr_variations(self):
        assert _map_column_to_field("cefr") == "cefr_level"
        assert _map_column_to_field("cefr_level") == "cefr_level"

    def test_jlpt_variations(self):
        assert _map_column_to_field("jlpt") == "jlpt_level"
        assert _map_column_to_field("jlpt_level") == "jlpt_level"

    def test_pos_variations(self):
        assert _map_column_to_field("part_of_speech") == "part_of_speech"
        assert _map_column_to_field("pos") == "part_of_speech"

    def test_unknown_column(self):
        assert _map_column_to_field("unknown") is None


class TestDetectEncodingAndDelimiter:
    def test_utf8_bom_stripped(self):
        content = b"\xef\xbb\xbfterm,language\nhello,en"
        text, delimiter = _detect_encoding_and_delimiter(content)
        assert text.startswith("term")
        assert delimiter == ","

    def test_tsv_detected(self):
        content = b"term\tlanguage\nhello\ten"
        text, delimiter = _detect_encoding_and_delimiter(content)
        assert delimiter == "\t"

    def test_csv_default(self):
        content = b"term,language\nhello,en"
        text, delimiter = _detect_encoding_and_delimiter(content)
        assert delimiter == ","


class TestParseRow:
    def test_valid_row(self):
        row = {"term": "hello", "language": "en", "definition": "A greeting"}
        result = _parse_row(row, 1)
        assert result.term == "hello"
        assert result.language == "en"
        assert result.definition == "A greeting"
        assert result.status == "valid"

    def test_missing_term(self):
        row = {"language": "en"}
        result = _parse_row(row, 1)
        assert result.status == "error"
        assert "term" in result.error_message.lower()

    def test_term_too_long(self):
        row = {"term": "a" * 101}
        result = _parse_row(row, 1)
        assert result.status == "error"
        assert "length" in result.error_message.lower()

    def test_html_tags_warning(self):
        row = {"term": "hello <b>world</b>"}
        result = _parse_row(row, 1)
        assert result.status == "warning"
        assert "html" in result.error_message.lower()

    def test_invalid_language_defaults_to_en(self):
        row = {"term": "hello", "language": "fr"}
        result = _parse_row(row, 1)
        assert result.status == "warning"
        assert result.language == "en"

    def test_valid_cefr_levels(self):
        for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
            row = {"term": "hello", "cefr_level": level}
            result = _parse_row(row, 1)
            assert result.cefr_level == level.upper()

    def test_invalid_cefr_warning(self):
        row = {"term": "hello", "cefr_level": "X9"}
        result = _parse_row(row, 1)
        assert result.status == "warning"
        assert "cefr" in result.error_message.lower()

    def test_valid_jlpt_levels(self):
        for level in ["N1", "N2", "N3", "N4", "N5"]:
            row = {"term": "hello", "jlpt_level": level}
            result = _parse_row(row, 1)
            assert result.jlpt_level == level.upper()

    def test_invalid_jlpt_warning(self):
        row = {"term": "hello", "jlpt_level": "N9"}
        result = _parse_row(row, 1)
        assert result.status == "warning"
        assert "jlpt" in result.error_message.lower()

    def test_hierarchical_tags_parsing(self):
        row = {"term": "hello", "tags": "Subject::Unit::Topic"}
        result = _parse_row(row, 1)
        assert result.tags == ["Subject", "Unit", "Topic"]

    def test_default_language_en(self):
        row = {"term": "hello"}
        result = _parse_row(row, 1)
        assert result.language == "en"


class TestParseCSV:
    def test_basic_csv_parsing(self):
        content = b"term,language,definition\nhello,en,A greeting"
        result = parse_csv(content)
        assert result.total_rows == 1
        assert result.valid_count == 1
        assert result.detected_columns == ["term", "language", "definition"]

    def test_tsv_parsing(self):
        content = b"term\tlanguage\tdefinition\nhello\ten\tA greeting"
        result = parse_csv(content)
        assert result.total_rows == 1
        assert result.valid_count == 1

    def test_utf8_bom_handling(self):
        content = b"\xef\xbb\xbfterm,language\nhello,en"
        result = parse_csv(content)
        assert result.total_rows == 1
        assert result.rows[0].term == "hello"

    def test_multiple_rows_with_mixed_status(self):
        content = b"term,language\nhello,en\n<html>tag,en\nalsoinvalid,fr\n"
        result = parse_csv(content)
        assert result.total_rows == 3
        assert result.valid_count == 1
        assert result.warning_count == 2
        assert result.error_count == 0

    def test_empty_file(self):
        content = b""
        result = parse_csv(content)
        assert result.total_rows == 0
        assert result.valid_count == 0

    def test_header_only(self):
        content = b"term,language,definition"
        result = parse_csv(content)
        assert result.total_rows == 0
        assert result.valid_count == 0

    def test_malformed_rows(self):
        content = b"term\nrow1\nrow2"
        result = parse_csv(content)
        assert result.total_rows >= 2

    def test_case_insensitive_headers(self):
        content = b"TERM,Language,DEFINITION\nhello,en,greeting"
        result = parse_csv(content)
        assert result.valid_count == 1
        assert result.rows[0].term == "hello"

    def test_row_number_tracking(self):
        content = b"term\nrow1\nrow2\nrow3"
        result = parse_csv(content)
        assert result.rows[0].row_number == 1
        assert result.rows[1].row_number == 2
        assert result.rows[2].row_number == 3
