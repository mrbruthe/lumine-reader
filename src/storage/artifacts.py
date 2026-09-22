import json
from pathlib import Path

from src.pipelines.document import (
    DocumentElement,
    ElementType,
    StructuredDocument,
    TableElement,
)
from src.tts.chunk import SpeechChunk
from src.tts.render import SpeechUnit, SpeechUnitType


def save_structured_document(
    document: StructuredDocument,
    output_path: str | Path,
) -> Path:
    """Persist a structured document as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    elements = []

    for element in document.elements:
        if isinstance(element, TableElement):
            elements.append(
                {
                    "type": ElementType.TABLE.value,
                    "rows": [list(row) for row in element.rows],
                }
            )
        else:
            elements.append(
                {
                    "type": element.type.value,
                    "text": element.text,
                    "level": element.level,
                }
            )

    payload = {"elements": elements}

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return path


def load_structured_document(
    input_path: str | Path,
) -> StructuredDocument:
    """Restore a structured document from JSON."""
    path = Path(input_path)

    payload = json.loads(path.read_text(encoding="utf-8"))

    elements: list[DocumentElement | TableElement] = []

    for item in payload["elements"]:
        element_type = ElementType(item["type"])

        if element_type == ElementType.TABLE:
            elements.append(
                TableElement(
                    rows=tuple(
                        tuple(row)
                        for row in item["rows"]
                    )
                )
            )
            continue

        elements.append(
            DocumentElement(
                type=element_type,
                text=item["text"],
                level=item.get("level"),
            )
        )

    return StructuredDocument(elements=tuple(elements))


def save_speech_units(
    units: tuple[SpeechUnit, ...],
    output_path: str | Path,
) -> Path:
    """Persist speech units as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "units": [
            {
                "type": unit.type.value,
                "text": unit.text,
                "level": unit.level,
            }
            for unit in units
        ]
    }

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return path


def load_speech_units(
    input_path: str | Path,
) -> tuple[SpeechUnit, ...]:
    """Restore speech units from JSON."""
    path = Path(input_path)

    payload = json.loads(path.read_text(encoding="utf-8"))

    return tuple(
        SpeechUnit(
            type=SpeechUnitType(item["type"]),
            text=item["text"],
            level=item.get("level"),
        )
        for item in payload["units"]
    )


def save_speech_chunks(
    chunks: tuple[SpeechChunk, ...],
    output_path: str | Path,
) -> Path:
    """Persist speech chunks as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "chunks": [
            {
                "index": chunk.index,
                "text": chunk.text,
                "units": [
                    {
                        "type": unit.type.value,
                        "text": unit.text,
                        "level": unit.level,
                    }
                    for unit in chunk.units
                ],
            }
            for chunk in chunks
        ]
    }

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return path


def load_speech_chunks(
    input_path: str | Path,
) -> tuple[SpeechChunk, ...]:
    """Restore speech chunks from JSON."""
    path = Path(input_path)

    payload = json.loads(path.read_text(encoding="utf-8"))

    return tuple(
        SpeechChunk(
            index=item["index"],
            text=item["text"],
            units=tuple(
                SpeechUnit(
                    type=SpeechUnitType(unit["type"]),
                    text=unit["text"],
                    level=unit.get("level"),
                )
                for unit in item["units"]
            ),
        )
        for item in payload["chunks"]
    )