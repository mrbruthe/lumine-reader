from src.pipelines.clean import (
    clean_text,
    normalize_markdown,
    normalize_quotes,
    normalize_unicode,
    normalize_whitespace,
    remove_html_tags,
    remove_page_numbers,
    repair_hyphenated_words,
    repair_line_breaks,
)


def test_normalize_unicode() -> None:
    result = normalize_unicode("ﬁnancial")
    assert result == "financial"


def test_normalize_quotes() -> None:
    text = "“Lumine Reader isn’t finished.”"

    result = normalize_quotes(text)

    assert result == '"Lumine Reader isn\'t finished."'


def test_repair_hyphenated_words() -> None:
    text = "Artificial intel-\nligence"

    result = repair_hyphenated_words(text)

    assert result == "Artificial intelligence"


def test_remove_page_numbers() -> None:
    text = "First paragraph.\n12\nSecond paragraph."

    result = remove_page_numbers(text)

    assert "12" not in result
    assert "First paragraph." in result
    assert "Second paragraph." in result


def test_remove_html_tags() -> None:
    text = "<p>This came from <strong>HTML</strong>.</p>"

    result = remove_html_tags(text)

    assert result == "This came from HTML."


def test_normalize_markdown_heading() -> None:
    text = "# Lumine Reader"

    result = normalize_markdown(text)

    assert result == "Lumine Reader"


def test_normalize_markdown_emphasis() -> None:
    text = "This is **important**."

    result = normalize_markdown(text)

    assert result == "This is important."


def test_markdown_link_is_preserved() -> None:
    text = "[Python](https://python.org)"

    result = normalize_markdown(text)

    assert result == text


def test_repair_line_breaks_preserves_paragraphs() -> None:
    text = "First line\ncontinues here.\n\nSecond paragraph."

    result = repair_line_breaks(text)

    assert result == (
        "First line continues here.\n\n"
        "Second paragraph."
    )


def test_normalize_whitespace() -> None:
    text = "Lumine     Reader\tpipeline"

    result = normalize_whitespace(text)

    assert result == "Lumine Reader pipeline"


def test_clean_text_preserves_semantic_content() -> None:
    text = """# Lumine Reader

12

Artificial intel-
ligence is changing the
way we process      information.

Read https://example.com

<p>This is **important**.</p>
"""

    result = clean_text(text)

    assert "Lumine Reader" in result
    assert "Artificial intelligence" in result
    assert "https://example.com" in result
    assert "This is important." in result
    assert "\n12\n" not in result