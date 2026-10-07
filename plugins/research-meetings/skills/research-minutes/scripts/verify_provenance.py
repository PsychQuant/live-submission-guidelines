#!/usr/bin/env python3
"""Check a minutes provenance file (JSONL) against the transcript it cites.

Usage:
    python3 -I verify_provenance.py <transcript.srt> <provenance.jsonl>

Each JSONL line is one claim in the minutes:
    {"id": "D2-3", "section": "二/（二）", "point": "...", "status": "attested",
     "cues": "1305-1317", "evidence": ["短引文一", "短引文二"], "note": "..."}

status is one of: attested, doc, inferred, supplement.
Only `attested` lines are checked against the transcript: `cues` must name cues
that exist, and every evidence string must appear verbatim in the text of that
cue range. `doc`, `inferred` and `supplement` lines must carry a non-empty
`note` saying where the claim comes from instead.

Exit code 0 when every line passes, 1 otherwise. A line that cannot be checked
is a failure, never a silent pass.
"""
import json
import re
import sys
from pathlib import Path

STATUSES = {'attested', 'doc', 'inferred', 'supplement'}
CUE_RE = re.compile(r'(\d+)\n(\d\d:\d\d:\d\d,\d{3}) --> \d\d:\d\d:\d\d,\d{3}\n(.*?)(?=\n\n\d+\n|\Z)', re.S)
MAX_EVIDENCE_CHARS = 40


def load_cues(srt_path):
    text = Path(srt_path).read_text(encoding='utf-8').replace('\r\n', '\n')
    return {int(m.group(1)): (m.group(2), m.group(3)) for m in CUE_RE.finditer(text)}


def parse_range(spec):
    m = re.fullmatch(r'\s*(\d+)\s*(?:[-–]\s*(\d+))?\s*', str(spec))
    if not m:
        return None
    a = int(m.group(1))
    b = int(m.group(2) or a)
    return (a, b) if a <= b else None


def check_line(rec, cues):
    problems = []
    status = rec.get('status')
    if status not in STATUSES:
        return [f'status 不是 {sorted(STATUSES)} 之一：{status!r}']
    if not rec.get('point'):
        problems.append('缺 point')
    if status != 'attested':
        if not rec.get('note'):
            problems.append(f'{status} 必須在 note 說明來源或推論內容')
        return problems
    rng = parse_range(rec.get('cues', ''))
    if rng is None:
        return problems + [f"cues 格式錯誤：{rec.get('cues')!r}"]
    missing = [i for i in range(rng[0], rng[1] + 1) if i not in cues]
    if missing:
        return problems + [f'cue 不存在：{missing[:5]}']
    span = '\n'.join(cues[i][1] for i in range(rng[0], rng[1] + 1))
    evidence = rec.get('evidence') or []
    if not evidence:
        problems.append('attested 至少要一段 evidence')
    for ev in evidence:
        if len(ev) > MAX_EVIDENCE_CHARS:
            problems.append(f'evidence 超過 {MAX_EVIDENCE_CHARS} 字（只放定位用短引文）：{ev[:20]}…')
        if ev not in span:
            problems.append(f'evidence 不在 cue {rng[0]}–{rng[1]} 內：{ev}')
    return problems


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    cues = load_cues(sys.argv[1])
    if not cues:
        print('✗ 逐字稿讀不到任何 cue')
        return 1
    failed = 0
    counts = {}
    lines = Path(sys.argv[2]).read_text(encoding='utf-8').splitlines()
    for n, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f'✗ 第 {n} 行不是合法 JSON：{e}')
            failed += 1
            continue
        counts[rec.get('status')] = counts.get(rec.get('status'), 0) + 1
        problems = check_line(rec, cues)
        if problems:
            failed += 1
            print(f"✗ {rec.get('id', f'line {n}')}：" + '；'.join(problems))
    total = sum(counts.values())
    summary = '、'.join(f'{k} {v}' for k, v in sorted(counts.items(), key=lambda kv: str(kv[0])))
    print(f'{total} 條（{summary}），{failed} 條未通過')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
