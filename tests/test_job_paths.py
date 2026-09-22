from src.storage.job_paths import get_job_paths


def test_get_job_paths(tmp_path):
    paths = get_job_paths(
        job_id="book-001",
        base_dir=tmp_path,
    )

    expected_root = tmp_path / "book-001"

    assert paths.root == expected_root
    assert paths.structured_document == expected_root / "structured_document.json"
    assert paths.speech_units == expected_root / "speech_units.json"
    assert paths.speech_chunks == expected_root / "chunks.json"
    assert paths.audio_dir == expected_root / "audio"
    assert paths.final_audio == expected_root / "final.mp3"