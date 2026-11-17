# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from rc_metastudio.macos_macho import MachOError, architectures


def _thin_macho(
    cpu_type: int,
    subtype: int,
    magic: bytes = b"\xcf\xfa\xed\xfe",
) -> bytes:
    byte_order = (
        "little" if magic in {b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe"} else "big"
    )
    header_size = 32 if magic in {b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe"} else 28
    return (
        magic
        + cpu_type.to_bytes(4, byte_order)
        + subtype.to_bytes(4, byte_order)
        + bytes(header_size - 12)
    )


def _fat_macho(
    architectures: list[tuple[int, int, bytes]],
    magic: bytes = b"\xca\xfe\xba\xbe",
    *,
    reserved: int = 0,
) -> bytes:
    byte_order = (
        "little" if magic in {b"\xbe\xba\xfe\xca", b"\xbf\xba\xfe\xca"} else "big"
    )
    entry_size = 32 if magic in {b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca"} else 20
    table_end = 8 + entry_size * len(architectures)
    offset = (table_end + 15) // 16 * 16
    entries = bytearray()
    slices = bytearray(offset - table_end)
    for cpu_type, subtype, payload in architectures:
        entries.extend(cpu_type.to_bytes(4, byte_order))
        entries.extend(subtype.to_bytes(4, byte_order))
        field_size = 8 if entry_size == 32 else 4
        entries.extend(offset.to_bytes(field_size, byte_order))
        entries.extend(len(payload).to_bytes(field_size, byte_order))
        entries.extend((4).to_bytes(4, byte_order))
        if entry_size == 32:
            entries.extend(reserved.to_bytes(4, byte_order))
        slices.extend(payload)
        offset += len(payload)
    return magic + len(architectures).to_bytes(4, byte_order) + entries + slices


def test_macho_architecture_parser_reads_thin_and_universal_without_lipo(
    tmp_path,
):
    for index, magic in enumerate((b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe")):
        thin = tmp_path / f"thin64-{index}"
        thin.write_bytes(_thin_macho(0x0100000C, 0, magic))
        assert architectures(thin) == ["arm64"]
    for index, magic in enumerate((b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe")):
        unsupported_thin = tmp_path / f"thin32-{index}"
        unsupported_thin.write_bytes(_thin_macho(7, 3, magic))
        with pytest.raises(MachOError, match="unsupported CPU type"):
            architectures(unsupported_thin)
    for index, magic in enumerate(
        (
            b"\xca\xfe\xba\xbe",
            b"\xbe\xba\xfe\xca",
            b"\xca\xfe\xba\xbf",
            b"\xbf\xba\xfe\xca",
        )
    ):
        universal = tmp_path / f"universal-{index}"
        universal.write_bytes(
            _fat_macho(
                [
                    (0x01000007, 3, _thin_macho(0x01000007, 3)),
                    (0x0100000C, 0, _thin_macho(0x0100000C, 0)),
                ],
                magic,
            )
        )
        assert architectures(universal) == ["arm64", "x86_64"]


def test_macho_architecture_parser_rejects_malformed_or_tampered_files(tmp_path):
    valid_arm = _thin_macho(0x0100000C, 0)
    malformed = [
        b"",
        b"not-macho",
        b"\xcf\xfa\xed\xfe" + (0x0100000C).to_bytes(4, "little"),
        b"\xcf\xfa\xed\xfe" + (1).to_bytes(4, "little") + bytes(24),
        b"\xca\xfe\xba\xbe" + (17).to_bytes(4, "big"),
        b"\xca\xfe\xba\xbe" + (2).to_bytes(4, "big") + bytes(20),
        (
            b"\xca\xfe\xba\xbe"
            + (1).to_bytes(4, "big")
            + (0x0100000C).to_bytes(4, "big")
            + bytes(4)
            + (4096).to_bytes(4, "big")
            + len(valid_arm).to_bytes(4, "big")
            + bytes(4)
        ),
        _fat_macho([(0x01000007, 3, valid_arm)]),
        _fat_macho(
            [
                (0x0100000C, 0, valid_arm),
                (0x0100000C, 0, valid_arm),
            ]
        ),
    ]
    for index, payload in enumerate(malformed):
        path = tmp_path / str(index)
        path.write_bytes(payload)
        with pytest.raises(MachOError, match="Mach-O file"):
            architectures(path)


def test_macho_architecture_parser_rejects_subtype_and_fat64_tampering(tmp_path):
    malformed = [
        (_thin_macho(0x01000007, 8), "unsupported x86_64 CPU subtype"),
        (_thin_macho(0x01000007, 0x40000003), "unsupported x86_64 CPU subtype"),
        (
            _fat_macho([(0x01000007, 3, _thin_macho(0x01000007, 0x80000003))]),
            "mismatched fat slice CPU identity",
        ),
        (
            _fat_macho([(0x01000007, 3, _thin_macho(0x01000007, 8))]),
            "unsupported x86_64 CPU subtype",
        ),
        (
            _fat_macho(
                [(0x0100000C, 0, _thin_macho(0x0100000C, 0))],
                b"\xca\xfe\xba\xbf",
                reserved=1,
            ),
            "nonzero fat64 reserved field",
        ),
    ]
    for index, (payload, expected_error) in enumerate(malformed):
        path = tmp_path / str(index)
        path.write_bytes(payload)
        with pytest.raises(MachOError, match=expected_error):
            architectures(path)
