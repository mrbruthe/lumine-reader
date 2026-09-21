import os
import subprocess
import tempfile
from pathlib import Path


def assemble_audio(
    chunk_paths: tuple[Path, ...],
    output_path: str | Path,
) -> Path:
    """Assemble ordered MP3 chunks into one final audiobook."""

    if not chunk_paths:
        raise ValueError("At least one audio chunk is required")

    chunks = tuple(Path(path) for path in chunk_paths)

    for path in chunks:
        if not path.exists():
            raise FileNotFoundError(f"Audio chunk not found: {path}")

        if path.stat().st_size == 0:
            raise ValueError(f"Audio chunk is empty: {path}")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # A non-empty final file represents completed assembly.
    if output_path.exists() and output_path.stat().st_size > 0:
        return output_path

    temp_output = output_path.with_name(
        f".{output_path.stem}.part{output_path.suffix}"
    )

    temp_output.unlink(missing_ok=True)

    manifest_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8",
        ) as manifest:
            manifest_path = Path(manifest.name)

            for path in chunks:
                absolute_path = path.resolve()
                escaped_path = str(absolute_path).replace("'", r"'\''")
                manifest.write(f"file '{escaped_path}'\n")

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(manifest_path),
                "-c",
                "copy",
                str(temp_output),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        if not temp_output.exists():
            raise RuntimeError("FFmpeg produced no assembled audio file")

        if temp_output.stat().st_size == 0:
            raise RuntimeError("FFmpeg produced an empty assembled audio file")

        os.replace(temp_output, output_path)

    except Exception:
        temp_output.unlink(missing_ok=True)
        raise

    finally:
        if manifest_path is not None:
            manifest_path.unlink(missing_ok=True)

    return output_path