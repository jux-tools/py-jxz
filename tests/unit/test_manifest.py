# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>

"""Tests for jxz.manifest module."""

from __future__ import annotations

import hashlib

import pytest
from hypothesis import given
from hypothesis import strategies as st

from jxz.errors import ManifestError
from jxz.manifest import Manifest, compute_digest, generate, parse

# --- Helpers ---

SPEC_EXAMPLE = """\
Manifest-Version: 1.0
Jux-Version: 1.0
Created-By: pytest-jux/0.1.0
Report-Type: pytest-junit
Timestamp: 2025-01-23T14:30:00Z

Name: junit.xml
SHA-256: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
Size: 4521

Name: attachments/test_login_screenshot.png
SHA-256: f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5
Size: 45231
Attachment-For: test_login
"""


def _make_main(**overrides: str) -> dict[str, str]:
    base = {
        "Manifest-Version": "1.0",
        "Jux-Version": "1.0",
        "Created-By": "test/1.0",
        "Report-Type": "pytest-junit",
        "Timestamp": "2026-01-01T00:00:00Z",
    }
    base.update(overrides)
    return base


def _make_entry(
    name: str = "junit.xml",
    digest: str = "a" * 64,
    size: str = "100",
    **extra: str,
) -> dict[str, str]:
    d: dict[str, str] = {"Name": name, "SHA-256": digest, "Size": size}
    d.update(extra)
    return d


# --- generate tests ---


class TestGenerate:
    def test_minimal_manifest(self) -> None:
        m = Manifest(main=_make_main(), entries=[_make_entry()])
        text = generate(m)
        assert "Manifest-Version: 1.0" in text
        assert "Name: junit.xml" in text

    def test_sections_separated_by_blank_lines(self) -> None:
        m = Manifest(main=_make_main(), entries=[_make_entry()])
        text = generate(m)
        # Main section followed by blank line, then entry section
        assert "\n\n" in text

    def test_trailing_newline(self) -> None:
        m = Manifest(main=_make_main(), entries=[_make_entry()])
        text = generate(m)
        assert text.endswith("\n")

    def test_multiple_entries(self) -> None:
        m = Manifest(
            main=_make_main(),
            entries=[
                _make_entry("junit.xml"),
                _make_entry("attachments/shot.png", size="200"),
            ],
        )
        text = generate(m)
        assert text.count("Name: ") == 2

    def test_extra_fields_preserved(self) -> None:
        m = Manifest(
            main={**_make_main(), "X-Custom": "value"},
            entries=[{**_make_entry(), "X-Extra": "data"}],
        )
        text = generate(m)
        assert "X-Custom: value" in text
        assert "X-Extra: data" in text


# --- parse tests ---


class TestParse:
    def test_spec_example(self) -> None:
        m = parse(SPEC_EXAMPLE)
        assert m.main["Manifest-Version"] == "1.0"
        assert m.main["Created-By"] == "pytest-jux/0.1.0"
        assert len(m.entries) == 2
        assert m.entries[0]["Name"] == "junit.xml"
        assert m.entries[1]["Attachment-For"] == "test_login"

    def test_empty_input(self) -> None:
        with pytest.raises(ManifestError, match="Empty manifest"):
            parse("")

    def test_whitespace_only(self) -> None:
        with pytest.raises(ManifestError, match="Empty manifest"):
            parse("   \n\n  ")

    def test_malformed_line(self) -> None:
        with pytest.raises(ManifestError, match="Malformed manifest line"):
            parse("this is not key-value\n")

    def test_missing_required_main_fields(self) -> None:
        text = "Manifest-Version: 1.0\n\n"
        with pytest.raises(ManifestError, match="Missing required main section"):
            parse(text)

    def test_missing_required_entry_fields(self) -> None:
        main_text = (
            "Manifest-Version: 1.0\n"
            "Jux-Version: 1.0\n"
            "Created-By: test/1.0\n"
            "Report-Type: pytest-junit\n"
            "Timestamp: 2026-01-01T00:00:00Z\n"
            "\n"
            "Name: junit.xml\n"
        )
        with pytest.raises(ManifestError, match="Missing required fields"):
            parse(main_text)

    def test_extra_fields_accepted(self) -> None:
        m = Manifest(
            main={**_make_main(), "X-Custom": "val"},
            entries=[{**_make_entry(), "X-Extra": "data"}],
        )
        text = generate(m)
        parsed = parse(text)
        assert parsed.main["X-Custom"] == "val"
        assert parsed.entries[0]["X-Extra"] == "data"

    def test_no_trailing_newline_still_works(self) -> None:
        m = Manifest(main=_make_main(), entries=[_make_entry()])
        text = generate(m).rstrip("\n")
        parsed = parse(text)
        assert parsed.main["Manifest-Version"] == "1.0"
        assert len(parsed.entries) == 1


# --- round-trip tests ---


class TestRoundTrip:
    def test_generate_parse_roundtrip(self) -> None:
        original = Manifest(
            main=_make_main(),
            entries=[
                _make_entry("junit.xml"),
                _make_entry(
                    "attachments/shot.png",
                    size="500",
                    **{"Attachment-For": "test_login"},
                ),
            ],
        )
        text = generate(original)
        recovered = parse(text)
        assert recovered.main == original.main
        assert recovered.entries == original.entries

    @given(
        extra_key=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"),
                min_codepoint=65,
                max_codepoint=122,
            ),
            min_size=1,
            max_size=20,
        ),
        extra_val=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"),
                min_codepoint=65,
                max_codepoint=122,
            ),
            min_size=1,
            max_size=50,
        ),
    )
    def test_roundtrip_with_extra_fields(self, extra_key: str, extra_val: str) -> None:
        original = Manifest(
            main={**_make_main(), f"X-{extra_key}": extra_val},
            entries=[_make_entry()],
        )
        text = generate(original)
        recovered = parse(text)
        assert recovered.main == original.main
        assert recovered.entries == original.entries


# --- compute_digest tests ---


class TestComputeDigest:
    def test_known_digest(self) -> None:
        data = b"hello world"
        expected = hashlib.sha256(data).hexdigest()
        assert compute_digest(data) == expected

    def test_empty_data(self) -> None:
        expected = hashlib.sha256(b"").hexdigest()
        assert compute_digest(b"") == expected

    def test_returns_lowercase_hex(self) -> None:
        result = compute_digest(b"test")
        assert result == result.lower()
        assert len(result) == 64
