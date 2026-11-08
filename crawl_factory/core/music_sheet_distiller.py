"""
Bộ Chưng Cất Bản Nhạc Ký Hiệu & Sinh Đa Định Dạng (`core/music_sheet_distiller.py`).

Giải quyết bài toán Bản quyền Hình ảnh Sheet nhạc & Tối ưu Dung lượng cho `fukuin`:
1. LOẠI BỎ 100% DỮ LIỆU CHẾ BẢN ĐỒ HỌA (Engraving / Layout Stripping):
   - Bỏ qua toàn bộ thông tin trình bày trang in của phần mềm Finale (`<defaults>`, `<page-layout>`,
     `<system-layout>`, `<appearance>`, `<credit>`, tọa độ `default-x`, `default-y`, phông chữ `Maestro`).
   - Chỉ trích xuất **Dữ liệu Âm nhạc Thuần túy (Pure Symbolic Musical Facts)** thuộc phạm vi công cộng:
     Nhịp (`time_signature`), Hóa biểu (`key_fifths`), Tempo (`tempo_bpm`), Hợp âm (`harmony`),
     và cao độ/trường độ của 4 bè hợp xướng (`Soprano`, `Alto`, `Tenor`, `Bass`).
2. CHUYỂN ĐỔI SANG 3 ĐỊNH DẠNG MỞ SIÊU NHẸ (Giảm 97%–99% dung lượng so với file XML 75 KB hoặc ảnh PNG 300 KB):
   - Định dạng 1 (`symbolic_score` JSON): Cấu trúc nốt nhạc 4 bè chuẩn hóa.
   - Định dạng 2 (`abc_notation` `.abc`, chỉ ~0.6–1.2 KB): Chuẩn ký hiệu bản nhạc ASCII mở (dùng `abcjs` trên web
     để vẽ lại sheet nhạc vector SVG mới hoàn toàn, hỗ trợ đổi tông Transpose trực tiếp và phóng to nốt nhạc
     cho người lớn tuổi theo chuẩn `kannert`).
   - Định dạng 3 (`Standard MIDI File .mid` Type 1 gồm 4 Track độc lập `Soprano`, `Alto`, `Tenor`, `Bass`,
     chỉ ~1.5 KB, sinh bằng Python thuần `struct`): Giúp ban hát Hội Thánh bật/tắt/tăng giảm âm lượng
     từng bè khi tập hát!
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
import struct
import xml.etree.ElementTree as ET

# Bảng ánh xạ số dấu thăng/giáng (fifths) sang tên giọng Trưởng (Major Key) trong chuẩn ABC Notation
FIFTHS_TO_ABC_KEY: Dict[int, str] = {
    -7: "Cb", -6: "Gb", -5: "Db", -4: "Ab", -3: "Eb", -2: "Bb", -1: "F",
    0: "C",
    1: "G", 2: "D", 3: "A", 4: "E", 5: "B", 6: "F#", 7: "C#",
}

# Thứ tự xuất hiện dấu thăng (Sharps) và dấu giáng (Flats) trên hóa biểu
SHARP_ORDER: List[str] = ["F", "C", "G", "D", "A", "E", "B"]
FLAT_ORDER: List[str] = ["B", "E", "A", "D", "G", "C", "F"]

# Bảng ánh xạ tên nốt (C..B) sang bán âm trong 1 quãng tám (C = 0)
STEP_TO_SEMITONE: Dict[str, int] = {
    "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11,
}


def key_default_alterations(fifths: int) -> Dict[str, int]:
    """Trả về bảng dấu hóa mặc định (`-1`, `0`, `+1`) của 7 bậc âm theo hóa biểu `fifths`."""
    alters = {s: 0 for s in STEP_TO_SEMITONE}
    if fifths > 0:
        for s in SHARP_ORDER[: min(7, fifths)]:
            alters[s] = 1
    elif fifths < 0:
        for s in FLAT_ORDER[: min(7, -fifths)]:
            alters[s] = -1
    return alters


def pitch_to_midi(step: str, octave: int, alter: int = 0) -> int:
    """Chuyển đổi `(step, octave, alter)` sang mã số nốt MIDI chuẩn (`C4 = 60`, `A4 = 69`)."""
    base = STEP_TO_SEMITONE.get(step.upper(), 0)
    return (octave + 1) * 12 + base + alter


def pitch_to_abc(step: str, octave: int, alter: int = 0, fifths: int = 0) -> str:
    """
    Chuyển đổi `(step, octave, alter)` sang ký hiệu nốt nhạc chuẩn ABC Notation,
    tự động đối chiếu hóa biểu (`fifths`) để chỉ ghi dấu hóa bất thường (`^`, `_`, `=`).
    """
    s = step.upper()
    default_alt = key_default_alterations(fifths).get(s, 0)
    acc = ""
    if alter != default_alt:
        if alter == 0:
            acc = "="
        elif alter > 0:
            acc = "^" * alter
        else:
            acc = "_" * (-alter)

    if octave <= 4:
        note_str = s
        if octave < 4:
            note_str += "," * (4 - octave)
    else:
        note_str = s.lower()
        if octave > 5:
            note_str += "'" * (octave - 5)
    return f"{acc}{note_str}"


def distill_musicxml_to_symbolic(xml_bytes_or_text: bytes | str) -> Dict[str, Any]:
    """
    Trích xuất dữ liệu âm nhạc thuần túy (4 bè SATB, nhịp, giọng, tempo, hợp âm) từ MusicXML,
    loại bỏ hoàn toàn thông tin chế bản đồ họa (`default-x`, `page-layout`...).
    """
    if isinstance(xml_bytes_or_text, bytes):
        root = ET.fromstring(xml_bytes_or_text)
    else:
        root = ET.fromstring(xml_bytes_or_text.encode("utf-8"))

    divisions = 2
    fifths = 0
    mode = "major"
    beats = 4
    beat_type = 4
    tempo_bpm = 100

    parts_data: Dict[str, List[Dict[str, Any]]] = {}

    for part_el in root.findall("part"):
        part_id = part_el.attrib.get("id", "P1")
        measures_out: List[Dict[str, Any]] = []

        for m_el in part_el.findall("measure"):
            m_num = m_el.attrib.get("number", "1")
            attr_el = m_el.find("attributes")
            if attr_el is not None:
                div_el = attr_el.find("divisions")
                if div_el is not None and div_el.text:
                    divisions = max(1, int(div_el.text.strip()))
                key_el = attr_el.find("key")
                if key_el is not None:
                    f_el = key_el.find("fifths")
                    if f_el is not None and f_el.text:
                        fifths = int(f_el.text.strip())
                    m_mode = key_el.find("mode")
                    if m_mode is not None and m_mode.text:
                        mode = m_mode.text.strip()
                time_el = attr_el.find("time")
                if time_el is not None:
                    b_el = time_el.find("beats")
                    bt_el = time_el.find("beat-type")
                    if b_el is not None and b_el.text and bt_el is not None and bt_el.text:
                        beats = int(b_el.text.strip())
                        beat_type = int(bt_el.text.strip())

            sound_el = m_el.find("sound")
            if sound_el is not None and "tempo" in sound_el.attrib:
                try:
                    tempo_bpm = int(float(sound_el.attrib["tempo"]))
                except ValueError:
                    pass

            chords_in_measure: List[str] = []
            for harm_el in m_el.findall("harmony"):
                r_step = harm_el.findtext("root/root-step", default="").strip()
                r_alter = harm_el.findtext("root/root-alter", default="").strip()
                kind_el = harm_el.find("kind")
                kind_txt = (kind_el.attrib.get("text") if kind_el is not None else "") or ""
                alter_sym = "#" if r_alter == "1" else ("b" if r_alter == "-1" else "")
                if r_step:
                    chords_in_measure.append(f"{r_step}{alter_sym}{kind_txt}")

            events: List[Dict[str, Any]] = []
            for note_el in m_el.findall("note"):
                if note_el.find("grace") is not None:
                    continue
                is_chord = note_el.find("chord") is not None
                is_rest = note_el.find("rest") is not None
                dur_raw = int(note_el.findtext("duration", default=str(divisions)).strip())
                voice = note_el.findtext("voice", default="1").strip()

                if is_rest:
                    events.append({
                        "is_rest": True,
                        "is_chord": False,
                        "voice": voice,
                        "duration_div": dur_raw,
                    })
                else:
                    step = note_el.findtext("pitch/step", default="C").strip()
                    octave = int(note_el.findtext("pitch/octave", default="4").strip())
                    alter = int(note_el.findtext("pitch/alter", default="0").strip())
                    midi_num = pitch_to_midi(step, octave, alter)
                    lyrics_map: Dict[str, str] = {}
                    for lyr_el in note_el.findall("lyric"):
                        l_num = lyr_el.attrib.get("number", "1")
                        l_txt = (lyr_el.findtext("text") or "").strip()
                        if l_txt:
                            lyrics_map[l_num] = l_txt

                    events.append({
                        "is_rest": False,
                        "is_chord": is_chord,
                        "voice": voice,
                        "step": step,
                        "octave": octave,
                        "alter": alter,
                        "midi": midi_num,
                        "duration_div": dur_raw,
                        "lyrics": lyrics_map if lyrics_map else None,
                    })

            measures_out.append({
                "measure": m_num,
                "chords": chords_in_measure,
                "events": events,
            })

        parts_data[part_id] = measures_out

    key_name = FIFTHS_TO_ABC_KEY.get(fifths, "C")
    if mode.lower() == "minor" and not key_name.endswith("m"):
        key_name += "m"

    return {
        "divisions": divisions,
        "key_fifths": fifths,
        "key_signature": key_name,
        "time_signature": f"{beats}/{beat_type}",
        "beats": beats,
        "beat_type": beat_type,
        "tempo_bpm": tempo_bpm,
        "measure_count": len(parts_data.get("P1", [])),
        "parts": parts_data,
    }


def symbolic_to_abc_notation(symbolic: Dict[str, Any], hymn_id: int, title: str, composer: str = "") -> str:
    """
    Chuyển đổi cấu trúc `symbolic` sang định dạng văn bản `ABC Music Notation` (`.abc` ~0.8 KB)
    cho giai điệu chính (Soprano + Hợp âm đệm + toàn bộ các câu lời) để render SVG động bằng `abcjs`.
    """
    div = max(1, int(symbolic.get("divisions", 2)))
    fifths = int(symbolic.get("key_fifths", 0))
    time_sig = symbolic.get("time_signature", "4/4")
    key_sig = symbolic.get("key_signature", "C")
    tempo = int(symbolic.get("tempo_bpm", 100))

    header_lines = [
        f"X:{hymn_id}",
        f"T:{title}",
    ]
    if composer:
        header_lines.append(f"C:{composer}")
    header_lines.extend([
        f"M:{time_sig}",
        f"L:1/{div * 4}",
        f"Q:1/4={tempo}",
        f"K:{key_sig}",
    ])

    p1_measures = symbolic.get("parts", {}).get("P1", [])
    abc_measures: List[str] = []
    lyrics_by_verse: Dict[str, List[str]] = {}

    for m in p1_measures:
        m_tokens: List[str] = []
        chords = m.get("chords", [])
        chord_idx = 0

        grouped_steps: List[List[Dict[str, Any]]] = []
        for ev in m.get("events", []):
            if ev.get("voice", "1") != "1":
                continue
            if ev.get("is_chord") and grouped_steps:
                grouped_steps[-1].append(ev)
            else:
                grouped_steps.append([ev])

        for group in grouped_steps:
            top_ev = max(group, key=lambda x: x.get("midi", 0))
            dur = int(top_ev.get("duration_div", div))
            dur_str = str(dur) if dur != 1 else ""
            chord_prefix = f'"{chords[chord_idx]}"' if chord_idx < len(chords) else ""
            if chord_idx < len(chords):
                chord_idx += 1

            if top_ev.get("is_rest"):
                m_tokens.append(f"{chord_prefix}z{dur_str}")
            else:
                abc_pitch = pitch_to_abc(top_ev["step"], top_ev["octave"], top_ev.get("alter", 0), fifths=fifths)
                m_tokens.append(f"{chord_prefix}{abc_pitch}{dur_str}")
                # Thu thập lời của tất cả các câu (verse 1..N) gắn với chùm nốt này
                verse_map_here: Dict[str, str] = {}
                for g_ev in group:
                    if g_ev.get("lyrics"):
                        for v_num, v_txt in g_ev["lyrics"].items():
                            if v_num not in verse_map_here:
                                verse_map_here[v_num] = v_txt
                for v_num, v_txt in verse_map_here.items():
                    lyrics_by_verse.setdefault(v_num, []).append(v_txt)

        if m_tokens:
            abc_measures.append(" ".join(m_tokens))

    body_line = " | ".join(abc_measures) + " |]"
    lines = header_lines + [body_line]
    for v_num in sorted(lyrics_by_verse.keys(), key=lambda x: int(x) if x.isdigit() else 99):
        if lyrics_by_verse[v_num]:
            lines.append("w: " + " ".join(lyrics_by_verse[v_num]))
    return "\n".join(lines) + "\n"


def _encode_varlen(value: int) -> bytes:
    """Mã hóa số nguyên Variable-Length Quantity (VLQ) chuẩn của định dạng Standard MIDI File."""
    val = max(0, int(value))
    buf = [val & 0x7F]
    val >>= 7
    while val > 0:
        buf.append((val & 0x7F) | 0x80)
        val >>= 7
    buf.reverse()
    return bytes(buf)


def _build_single_voice_track(
    track_name: str,
    channel: int,
    measures: List[Dict[str, Any]],
    pick_high: bool,
    divisions: int,
    tick_scale: int,
) -> bytes:
    """Sinh 1 Track MIDI độc lập cho 1 bè hợp xướng (`Soprano`, `Alto`, `Tenor`, hoặc `Bass`)."""
    tr = bytearray()
    # Meta Event 0x03: Sequence/Track Name
    name_bytes = track_name.encode("ascii", errors="ignore")
    tr.extend(b"\x00\xff\x03" + _encode_varlen(len(name_bytes)) + name_bytes)
    # Program Change: Acoustic Grand Piano (0)
    tr.extend(b"\x00" + bytes([0xC0 | (channel & 0x0F), 0]))

    for m in measures:
        voice_1_groups: List[List[Dict[str, Any]]] = []
        for ev in m.get("events", []):
            if ev.get("voice", "1") != "1":
                continue
            if ev.get("is_chord") and voice_1_groups:
                voice_1_groups[-1].append(ev)
            else:
                voice_1_groups.append([ev])

        for group in voice_1_groups:
            dur_ticks = max(1, int(group[0].get("duration_div", divisions)) * tick_scale)
            pitched = [ev for ev in group if not ev.get("is_rest") and "midi" in ev]
            if not pitched:
                # Nghỉ (Rest)
                tr.extend(_encode_varlen(0) + bytes([0x90 | channel, 60, 0]))
                tr.extend(_encode_varlen(dur_ticks) + bytes([0x80 | channel, 60, 0]))
            else:
                chosen = max(pitched, key=lambda x: x["midi"]) if pick_high else min(pitched, key=lambda x: x["midi"])
                m_note = chosen["midi"] & 0x7F
                velocity = 88 if pick_high else 74
                tr.extend(_encode_varlen(0) + bytes([0x90 | channel, m_note, velocity]))
                tr.extend(_encode_varlen(dur_ticks) + bytes([0x80 | channel, m_note, 0]))

    tr.extend(b"\x00\xff\x2f\x00")
    return bytes(tr)


def symbolic_to_midi_bytes(symbolic: Dict[str, Any]) -> bytes:
    """
    Sinh trực tiếp file nhị phân `Standard MIDI File (.mid)` Type 1 đa kênh (4 bè SATB độc lập)
    từ dữ liệu `symbolic` chỉ bằng thư viện chuẩn `struct` của Python (0 phụ thuộc ngoài!):
    - Track 0: Tempo & Time Signature Meta Track
    - Track 1 (Channel 0): `Soprano` (Bè Nữ Cao - lấy từ nốt cao của P1)
    - Track 2 (Channel 1): `Alto` (Bè Nữ Trầm - lấy từ nốt thấp của P1)
    - Track 3 (Channel 2): `Tenor` (Bè Nam Cao - lấy từ nốt cao của P2)
    - Track 4 (Channel 3): `Bass` (Bè Nam Trầm - lấy từ nốt thấp của P2)
    """
    divisions = max(1, int(symbolic.get("divisions", 2)))
    ticks_per_quarter = 480
    tick_scale = ticks_per_quarter // divisions
    tempo_bpm = max(30, int(symbolic.get("tempo_bpm", 100)))
    mpqn = int(60_000_000 / tempo_bpm)

    tracks_binary: List[bytes] = []

    # --- Track 0: Meta Track (Tempo) ---
    t0 = bytearray()
    t0.extend(b"\x00\xff\x51\x03" + mpqn.to_bytes(3, "big"))
    t0.extend(b"\x00\xff\x2f\x00")
    tracks_binary.append(bytes(t0))

    parts = symbolic.get("parts", {})
    p1 = parts.get("P1", [])
    p2 = parts.get("P2", [])

    if p1:
        tracks_binary.append(_build_single_voice_track("Soprano", 0, p1, True, divisions, tick_scale))
        tracks_binary.append(_build_single_voice_track("Alto", 1, p1, False, divisions, tick_scale))
    if p2:
        tracks_binary.append(_build_single_voice_track("Tenor", 2, p2, True, divisions, tick_scale))
        tracks_binary.append(_build_single_voice_track("Bass", 3, p2, False, divisions, tick_scale))

    out = bytearray()
    out.extend(b"MThd")
    out.extend(struct.pack(">IHHH", 6, 1, len(tracks_binary), ticks_per_quarter))
    for tb in tracks_binary:
        out.extend(b"MTrk")
        out.extend(struct.pack(">I", len(tb)))
        out.extend(tb)
    return bytes(out)


def distill_musicxml_file(
    xml_path: str | Path,
    hymn_id: int,
    title: str,
    composer: str = "",
    abc_out_path: Optional[str | Path] = None,
    midi_out_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """
    Hàm tiện ích trọn gói: Đọc file MusicXML thô, loại bỏ hoàn toàn phần chế bản đồ họa,
    xuất ra file `.abc` + file `.mid` 4 bè SATB (nếu truyền đường dẫn), và trả về dictionary kết quả.
    """
    p = Path(xml_path)
    raw_bytes = p.read_bytes()
    symbolic = distill_musicxml_to_symbolic(raw_bytes)
    abc_str = symbolic_to_abc_notation(symbolic, hymn_id=hymn_id, title=title, composer=composer)
    midi_bytes = symbolic_to_midi_bytes(symbolic)

    if abc_out_path is not None:
        abc_p = Path(abc_out_path)
        abc_p.parent.mkdir(parents=True, exist_ok=True)
        abc_p.write_text(abc_str, encoding="utf-8")

    if midi_out_path is not None:
        mid_p = Path(midi_out_path)
        mid_p.parent.mkdir(parents=True, exist_ok=True)
        mid_p.write_bytes(midi_bytes)

    return {
        "key_signature": symbolic["key_signature"],
        "time_signature": symbolic["time_signature"],
        "tempo_bpm": symbolic["tempo_bpm"],
        "measure_count": symbolic["measure_count"],
        "abc_notation": abc_str,
        "abc_size_bytes": len(abc_str.encode("utf-8")),
        "midi_size_bytes": len(midi_bytes),
        "raw_xml_size_bytes": len(raw_bytes),
    }
