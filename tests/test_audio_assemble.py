from pathlib import Path
import subprocess

import pytest

from src.audio.assemble import assemble_audio


def create_chunk(path: Path, content: bytes = b"audio") -> Path:
    """Create a non-empty fake audio chunk."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_no_chunks_raises_error(tmp_path):
    output_path = tmp_path / "final.mp3"

    with pytest.raises(
        ValueError,
        match="At least one audio chunk is required",
    ):
        assemble_audio((), output_path)


def test_missing_chunk_raises_error(tmp_path):
    missing_chunk = tmp_path / "0000.mp3"
    output_path = tmp_path / "final.mp3"

    with pytest.raises(FileNotFoundError):
        assemble_audio(
            (missing_chunk,),
            output_path,
        )


def test_empty_chunk_raises_error(tmp_path):
    chunk = tmp_path / "0000.mp3"
    chunk.touch()

    output_path = tmp_path / "final.mp3"

    with pytest.raises(
        ValueError,
        match="Audio chunk is empty",
    ):
        assemble_audio(
            (chunk,),
            output_path,
        )


def test_existing_completed_output_is_skipped(
    tmp_path,
    monkeypatch,
):
    chunk = create_chunk(tmp_path / "0000.mp3")

    output_path = tmp_path / "final.mp3"
    output_path.write_bytes(b"completed")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("FFmpeg should not be called")

    monkeypatch.setattr(
        subprocess,
        "run",
        fail_if_called,
    )

    result = assemble_audio(
        (chunk,),
        output_path,
    )

    assert result == output_path
    assert output_path.read_bytes() == b"completed"


def test_ffmpeg_is_called_with_chunks_in_order(
    tmp_path,
    monkeypatch,
):
    first = create_chunk(tmp_path / "0000.mp3")
    second = create_chunk(tmp_path / "0001.mp3")
    third = create_chunk(tmp_path / "0002.mp3")

    output_path = tmp_path / "final.mp3"

    observed_manifest = ""

    def fake_run(command, **kwargs):
        nonlocal observed_manifest

        manifest_path = Path(
            command[command.index("-i") + 1]
        )

        observed_manifest = manifest_path.read_text(
            encoding="utf-8"
        )

        Path(command[-1]).write_bytes(b"assembled")

        return subprocess.CompletedProcess(
            command,
            0,
        )

    monkeypatch.setattr(
        subprocess,
        "run",
        fake_run,
    )

    assemble_audio(
        (first, second, third),
        output_path,
    )

    first_position = observed_manifest.index(
        str(first.resolve())
    )
    second_position = observed_manifest.index(
        str(second.resolve())
    )
    third_position = observed_manifest.index(
        str(third.resolve())
    )

    assert first_position < second_position < third_position


def test_successful_assembly_creates_final_output(
    tmp_path,
    monkeypatch,
):
    chunk = create_chunk(tmp_path / "0000.mp3")
    output_path = tmp_path / "final.mp3"

    def fake_run(command, **kwargs):
        Path(command[-1]).write_bytes(b"assembled audio")

        return subprocess.CompletedProcess(
            command,
            0,
        )

    monkeypatch.setattr(
        subprocess,
        "run",
        fake_run,
    )

    result = assemble_audio(
        (chunk,),
        output_path,
    )

    assert result == output_path
    assert output_path.read_bytes() == b"assembled audio"


def test_failed_assembly_removes_partial_output(
    tmp_path,
    monkeypatch,
):
    chunk = create_chunk(tmp_path / "0000.mp3")
    output_path = tmp_path / "final.mp3"

    def fake_run(command, **kwargs):
        Path(command[-1]).write_bytes(b"partial")

        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=command,
        )

    monkeypatch.setattr(
        subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(subprocess.CalledProcessError):
        assemble_audio(
            (chunk,),
            output_path,
        )

    assert not output_path.exists()

    partial_path = output_path.with_name(
        f".{output_path.stem}.part{output_path.suffix}"
    )

    assert not partial_path.exists()


def test_empty_ffmpeg_output_is_rejected(
    tmp_path,
    monkeypatch,
):
    chunk = create_chunk(tmp_path / "0000.mp3")
    output_path = tmp_path / "final.mp3"

    def fake_run(command, **kwargs):
        Path(command[-1]).touch()

        return subprocess.CompletedProcess(
            command,
            0,
        )

    monkeypatch.setattr(
        subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(
        RuntimeError,
        match="FFmpeg produced an empty assembled audio file",
    ):
        assemble_audio(
            (chunk,),
            output_path,
        )

    assert not output_path.exists()