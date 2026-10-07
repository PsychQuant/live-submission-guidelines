#!/usr/bin/env bash
# 編譯研究會議紀錄 .tex（XeLaTeX 標楷體）並做品質檢查。
# 用法：compile.sh <會議名>_會議紀錄_<YYYY-MM-DD>.tex
# 產出：同目錄的 .pdf；stdout 印出 error／缺字／頁數／語體檢查／各頁末行。
#
# 改編自 sinica-admin meeting-minutes 的 scripts/compile.sh（0.32.15）。與原版的差別：
#   - 缺字（tofu）由警告改為失敗：缺字代表 PDF 上那個字印不出來。
#   - 加兩道失敗閘：製作方法詞入正文、模板佔位符（<…>）未填。
#   - 印出每頁末行，供檢查標題是否落單在頁尾。
#   - 編譯 log 放 mktemp 目錄，不寫固定的 /tmp 路徑。
# 原版的檢查邏輯改了時，回頭比對這裡是否要跟著改。
#
# 所有語體檢查都只掃正文：從未被跳脫的 % 起到行末屬註解，不進 PDF，不該被判違規。
set -euo pipefail

TEX="${1:?用法: compile.sh <path/to/會議紀錄.tex>}"
[ -f "$TEX" ] || { echo "✗ 找不到檔案：$TEX" >&2; exit 1; }
command -v xelatex >/dev/null || { echo "✗ 需要 xelatex（TeX Live）" >&2; exit 1; }
command -v pdfinfo >/dev/null || { echo "✗ 需要 pdfinfo／pdftotext（poppler）" >&2; exit 1; }

DIR="$(cd "$(dirname "$TEX")" && pwd)"
BASE="$(basename "$TEX" .tex)"
LOGDIR="$(mktemp -d "${TMPDIR:-/tmp}/research-minutes.XXXXXX")"
cd "$DIR"

run() { xelatex -interaction=nonstopmode -halt-on-error "$BASE.tex" > "$LOGDIR/run$1.log" 2>&1; }
run 1 || { echo "✗ 第 1 次 xelatex 失敗（log：$LOGDIR/run1.log）"; grep -nE '^! ' "$LOGDIR/run1.log" | head; exit 1; }
run 2 || { echo "✗ 第 2 次 xelatex 失敗（log：$LOGDIR/run2.log）"; grep -nE '^! ' "$LOGDIR/run2.log" | head; exit 1; }

LOG="$LOGDIR/run2.log"
ERRORS=$(grep -cE '^! ' "$LOG" || true)
TOFU=$(grep -c 'Missing character' "$LOG" || true)
PAGES=$(pdfinfo "$BASE.pdf" 2>/dev/null | awk '/^Pages/{print $2}')

strip_comments() {
  awk '{
    out = ""
    for (i = 1; i <= length($0); i++) {
      c = substr($0, i, 1)
      if (c == "%" && (i == 1 || substr($0, i-1, 1) != "\\")) break
      out = out c
    }
    print out
  }' "$1"
}
BODY=$(strip_comments "$BASE.tex")
count() { printf '%s\n' "$BODY" | grep -cE "$1" || true; }
show() { strip_comments "$BASE.tex" | grep -nE "$1" | sed 's/\(.\{90\}\).*/\1…/' | sed 's/^/     /' | head -6 || true; }

DASH=$(count '——|—')
MDBOLD=$(count '\*\*')
MDTICK=$(count '`')
NOUNMIS=$(count '會議記錄|記錄：')
PROCESS=$(count '語音辨識|逐字稿|字錯誤率|ASR|diarization|聲紋')
TEMPLATE=$(printf '%s\n' "$BODY" | python3 -I -c 'import re,sys; print(sum(1 for l in sys.stdin if re.search(r"<[^<>$]*[一-鿿][^<>$]*>", l)))')
# 只抓地名的「台」，不抓人名（如「陳東台」）：與 sinica-admin 原版同一判準
TAI=$(count '台灣|台北|台中|台南|台大')
META=$(count '未能查得|未能確認|因錄音不清|錄音不清|記錄者未能|無從查證')
# pipefail 下 grep 找不到會讓整個指派失敗、set -e 靜默結束腳本；|| true 必要
PLACEHOLDERS=$( { printf '%s\n' "$BODY" | grep -o '〔待補[^〕]*〕' || true; } | wc -l | tr -d ' ')

echo "✓ 編譯完成：${DIR}/${BASE}.pdf"
echo "   errors: ${ERRORS} | 缺字: ${TOFU} | pages: ${PAGES:-?} | 〔待補〕: ${PLACEHOLDERS}"
echo "   語體（僅正文）：破折號 ${DASH} | md 粗體 ${MDBOLD} | backtick ${MDTICK} | 記錄/紀錄 ${NOUNMIS} | 製作方法詞 ${PROCESS} | 未填佔位符 ${TEMPLATE} | 「台」${TAI} | 查證狀態 ${META}"

FAIL=0
[ "$ERRORS" = "0" ] || FAIL=1
if [ "$TOFU" != "0" ]; then
  echo "   ✗ 缺字 ${TOFU} 處：BiauKai 沒有該字符（常見：希臘字母、上標、○）。希臘字母與上標改用數學模式（\$\\eta^2\$、\$\\alpha\$）。"
  grep 'Missing character' "$LOG" | sed 's/^/     /' | head -5 || true
  FAIL=1
fi
if [ "$DASH" != "0" ]; then
  echo "   ✗ 破折號 ${DASH} 處：把兩個成分黏在一起而不交代關係。改用句號分句、冒號帶出說明。"
  show '——|—'; FAIL=1
fi
if [ "$MDBOLD" != "0" ] || [ "$MDTICK" != "0" ]; then
  echo "   ✗ markdown 語法殘留（粗體 ${MDBOLD}、backtick ${MDTICK}），LaTeX 會原樣印出。要突出就改寫句子。"
  show '\*\*|`'; FAIL=1
fi
if [ "$NOUNMIS" != "0" ]; then
  echo "   ✗ 名詞用「紀錄」：文件名稱與欄位標籤是名詞，寫「會議紀錄」「紀錄：」。"
  show '會議記錄|記錄：'; FAIL=1
fi
if [ "$PROCESS" != "0" ]; then
  echo "   ✗ 製作方法詞入正文 ${PROCESS} 處：轉錄、校對的過程寫進 % 註解或溯源檔，不寫進紀錄。"
  show '語音辨識|逐字稿|字錯誤率|ASR|diarization|聲紋'; FAIL=1
fi
if [ "$TEMPLATE" != "0" ]; then
  echo "   ✗ 模板佔位符未填 ${TEMPLATE} 處（<…>）。不知道的事寫〔待補：…〕，交使用者補。"
  FAIL=1
fi
if [ "$TAI" != "0" ]; then
  echo "   ⚠ 「台」${TAI} 處：一般用字寫「臺」；人名、機關原名照原寫法，確認後可忽略。"
fi
if [ "$META" != "0" ]; then
  echo "   ⚠ 正文出現查證失敗狀態 ${META} 處：出處留，「查不到」放溯源檔；會影響行動時改寫成行動式表述。"
fi
if [ "$PLACEHOLDERS" != "0" ]; then
  echo "   ⚠ 〔待補〕${PLACEHOLDERS} 處：交付時逐一列給使用者。"
fi

echo "   各頁末行（不應是標題）："
for pg in $(seq 1 "${PAGES:-0}"); do
  last=$(pdftotext -f "$pg" -l "$pg" "$BASE.pdf" - | grep -v '^[[:space:]]*$' | grep -vE '^[[:space:]]*[0-9]+[[:space:]]*$' | tail -1 || true)
  echo "     p$pg: ${last:0:50}"
done

exit "$FAIL"
