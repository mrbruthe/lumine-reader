import re
from dataclasses import dataclass
from enum import Enum

from src.pipelines.document import (
    DocumentElement,
    ElementType,
    StructuredDocument,
    TableElement,
)
from src.tts.normalize import normalize_for_tts, narrate_table


class SpeechUnitType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"


@dataclass(frozen=True)
class SpeechUnit:
    type: SpeechUnitType
    text: str
    level: int | None = None


def normalize_heading_for_speech(text: str) -> str:
    """Add a natural speech boundary after hierarchical heading numbers."""

    return re.sub(
        r"^(\d+(?:\.\d+)+)\s+",
        r"\1. ",
        text,
    )


def render_document(document: StructuredDocument) -> tuple[SpeechUnit, ...]:
    """Convert a structured document into ordered speech units."""

    units: list[SpeechUnit] = []

    for element in document.elements:
        if isinstance(element, TableElement):
            text = narrate_table(element)

            if text:
                units.append(
                    SpeechUnit(
                        type=SpeechUnitType.TABLE,
                        text=text,
                    )
                )

            continue

        text = normalize_for_tts(element.text)

        if not text:
            continue

        if element.type == ElementType.HEADING:
            text = normalize_heading_for_speech(text)
            unit_type = SpeechUnitType.HEADING
        else:
            unit_type = SpeechUnitType.PARAGRAPH

        units.append(
            SpeechUnit(
                type=unit_type,
                text=text,
                level=element.level,
            )
        )

    return tuple(units)