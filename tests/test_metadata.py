from src.pipelines.document import (
    DocumentElement,
    ElementType,
    StructuredDocument,
)
from src.pipelines.metadata import (
    BookMetadata,
    MetadataSource,
    extract_book_metadata,
)


def test_explicit_metadata_has_highest_priority():
    document = StructuredDocument(
        elements=(
            DocumentElement(
                type=ElementType.HEADING,
                text="A Different Title",
                level=1,
            ),
        )
    )

    metadata = extract_book_metadata(
        document=document,
        source_filename="fallback-book.pdf",
        explicit_title="The Hidden Power",
        explicit_author="Thomas Troward",
    )

    assert metadata.title == "The Hidden Power"
    assert metadata.author == "Thomas Troward"
    assert metadata.title_source == MetadataSource.EXPLICIT
    assert metadata.author_source == MetadataSource.EXPLICIT


def test_title_can_be_detected_from_first_heading():
    document = StructuredDocument(
        elements=(
            DocumentElement(
                type=ElementType.HEADING,
                text="The Creative Process",
                level=1,
            ),
            DocumentElement(
                type=ElementType.PARAGRAPH,
                text="This is the opening paragraph.",
            ),
        )
    )

    metadata = extract_book_metadata(
        document=document,
        source_filename="book.pdf",
    )

    assert metadata.title == "The Creative Process"
    assert metadata.title_source == MetadataSource.STRUCTURED


def test_author_can_be_detected_from_front_matter():
    document = StructuredDocument(
        elements=(
            DocumentElement(
                type=ElementType.HEADING,
                text="The Creative Process",
                level=1,
            ),
            DocumentElement(
                type=ElementType.PARAGRAPH,
                text="By Thomas Troward",
            ),
            DocumentElement(
                type=ElementType.PARAGRAPH,
                text="Chapter One begins here.",
            ),
        )
    )

    metadata = extract_book_metadata(
        document=document,
        source_filename="book.pdf",
    )

    assert metadata.author == "Thomas Troward"
    assert metadata.author_source == MetadataSource.STRUCTURED


def test_filename_is_used_as_title_fallback():
    document = StructuredDocument(elements=())

    metadata = extract_book_metadata(
        document=document,
        source_filename="the-hidden-power.pdf",
    )

    assert metadata.title == "the-hidden-power"
    assert metadata.title_source == MetadataSource.FILENAME


def test_unknown_author_is_not_guessed():
    document = StructuredDocument(
        elements=(
            DocumentElement(
                type=ElementType.PARAGRAPH,
                text="This book discusses the nature of thought.",
            ),
        )
    )

    metadata = extract_book_metadata(
        document=document,
        source_filename="mental-science.pdf",
    )

    assert metadata.author is None
    assert metadata.author_source is None


def test_source_filename_is_preserved():
    document = StructuredDocument(elements=())

    metadata = extract_book_metadata(
        document=document,
        source_filename="my-book.epub",
    )

    assert metadata.source_filename == "my-book.epub"


def test_book_metadata_is_immutable():
    metadata = BookMetadata(
        title="Example",
        author="Example Author",
        source_filename="example.pdf",
        title_source=MetadataSource.EXPLICIT,
        author_source=MetadataSource.EXPLICIT,
    )

    assert metadata.title == "Example"
    assert metadata.author == "Example Author"