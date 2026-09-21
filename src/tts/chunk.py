import re
from dataclasses import dataclass

from src.tts.render import SpeechUnit, SpeechUnitType


@dataclass(frozen=True)
class SpeechChunk:
    index: int
    units: tuple[SpeechUnit, ...]
    text: str


def speech_text_for_unit(unit: SpeechUnit) -> str:
    """Render a speech unit for TTS while preserving semantic boundaries."""

    text = unit.text.strip()

    if (
        unit.type == SpeechUnitType.HEADING
        and text
        and text[-1] not in ".!?:;"
    ):
        return f"{text}."

    return text


def split_by_words(text: str, max_chars: int) -> tuple[str, ...]:
    """Split text at word boundaries, using hard splits only when necessary."""

    text = text.strip()

    if not text:
        return ()

    if len(text) <= max_chars:
        return (text,)

    words = text.split()

    parts: list[str] = []
    current = ""

    for word in words:
        # A single token may itself exceed the limit.
        if len(word) > max_chars:
            if current:
                parts.append(current)
                current = ""

            parts.extend(
                word[start:start + max_chars]
                for start in range(0, len(word), max_chars)
            )
            continue

        candidate = f"{current} {word}".strip()

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                parts.append(current)

            current = word

    if current:
        parts.append(current)

    return tuple(parts)


def split_oversized_text(
    text: str,
    max_chars: int,
) -> tuple[str, ...]:
    """Split oversized text at sentence, then word boundaries."""

    text = text.strip()

    if not text:
        return ()

    if len(text) <= max_chars:
        return (text,)

    sentences = re.split(r"(?<=[.!?])\s+", text)

    parts: list[str] = []
    current = ""

    for sentence in sentences:
        # A single sentence is too large, so fall back to words.
        if len(sentence) > max_chars:
            if current:
                parts.append(current)
                current = ""

            parts.extend(
                split_by_words(
                    sentence,
                    max_chars,
                )
            )
            continue

        candidate = f"{current} {sentence}".strip()

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                parts.append(current)

            current = sentence

    if current:
        parts.append(current)

    return tuple(parts)


def chunk_speech_units(
    units: tuple[SpeechUnit, ...],
    max_chars: int = 3000,
) -> tuple[SpeechChunk, ...]:
    """Create bounded speech chunks while preserving semantic boundaries."""

    if max_chars <= 0:
        raise ValueError(
            "max_chars must be greater than zero"
        )

    chunks: list[SpeechChunk] = []

    current_units: list[SpeechUnit] = []
    current_texts: list[str] = []

    def flush() -> None:
        """Save the current chunk and reset the accumulator."""

        if not current_units:
            return

        chunks.append(
            SpeechChunk(
                index=len(chunks),
                units=tuple(current_units),
                text="\n\n".join(current_texts),
            )
        )

        current_units.clear()
        current_texts.clear()

    for unit in units:
        # Convert the semantic unit into its TTS-facing form.
        # Headings receive terminal punctuation when needed so
        # the speech engine produces a reliable boundary before
        # the following content.
        text = speech_text_for_unit(unit)

        if not text:
            continue

        # Oversized units cannot fit safely into a normal chunk.
        if len(text) > max_chars:
            flush()

            for part in split_oversized_text(
                text,
                max_chars,
            ):
                split_unit = SpeechUnit(
                    type=unit.type,
                    text=part,
                    level=unit.level,
                )

                chunks.append(
                    SpeechChunk(
                        index=len(chunks),
                        units=(split_unit,),
                        text=part,
                    )
                )

            continue

        # Preserve whole SpeechUnits whenever possible.
        projected_text = "\n\n".join(
            [*current_texts, text]
        )

        if (
            current_units
            and len(projected_text) > max_chars
        ):
            flush()

        current_units.append(unit)
        current_texts.append(text)

    flush()

    return tuple(chunks)