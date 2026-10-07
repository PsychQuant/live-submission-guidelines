#!/usr/bin/env python3
"""Style gate for research minutes written in Chinese Markdown.

Usage:
    python3 -I check_style.py <minutes.md> [--allow-tai 東台 --allow-tai 台大 ...]

Checks the rendered body only: HTML comments (<!-- ... -->) are stripped first,
because that is where production notes and removed passages are kept on purpose.

Closed list of checks (do not add a check here without a failure that motivated it):
  1. dash      no 「——」 or 「—」: write the relation between the two parts instead
  2. bold      no **bold** for emphasis (APA: rewrite the sentence instead)
  3. tai       「臺」 not 「台」, except inside names passed with --allow-tai
  4. jilu      the document and the recorder field are 「紀錄」 (noun), never 「會議記錄」 or 「記錄：」
  5. process   production details stay out of the body: 語音辨識, 逐字稿, ASR, 字錯誤率, diarization, 聲紋
Exit code 0 when all checks pass, 1 otherwise.
"""
import re
import sys
from pathlib import Path

PROCESS_TERMS = ['語音辨識', '逐字稿', 'ASR', '字錯誤率', 'diarization', '聲紋']


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    path, allow = args[0], []
    i = 1
    while i < len(args):
        if args[i] == '--allow-tai' and i + 1 < len(args):
            allow.append(args[i + 1])
            i += 2
        else:
            print(f'unknown argument: {args[i]}')
            return 2
    text = Path(path).read_text(encoding='utf-8')
    body = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    lines = body.split('\n')
    failures = []
    for n, line in enumerate(lines, 1):
        if re.search(r'——|—', line):
            failures.append(('dash', n, line))
        if '**' in line:
            failures.append(('bold', n, line))
        stripped = line
        for name in allow:
            stripped = stripped.replace(name, '')
        if '台' in stripped:
            failures.append(('tai', n, line))
        if re.search(r'會議記錄|記錄：', line):
            failures.append(('jilu', n, line))
        for term in PROCESS_TERMS:
            if term in line:
                failures.append(('process', n, line))
                break
    for kind, n, line in failures:
        print(f'✗ [{kind}] 第 {n} 行（去除註解後）：{line.strip()[:60]}')
    placeholders = re.findall(r'〔待補[^〕]*〕', body)
    print(f'{len(failures)} 項未通過；〔待補〕標記 {len(placeholders)} 處（交付前要逐一交使用者補齊）')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
