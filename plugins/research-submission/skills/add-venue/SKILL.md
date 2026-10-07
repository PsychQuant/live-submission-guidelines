---
name: add-venue
description: Use when a journal or conference is NOT yet in the research-submission corpus and needs to be added, or when an existing record must be re-fetched because verify.py reported CHANGED. Triggers on "把 <期刊> 加進來", "add <venue> to the corpus", "這個期刊還沒收錄", "收錄 <conference>", "來源變了要更新". Fetches the venue's primary sources, asserts fetch validity, and writes a schema-valid YAML record with full provenance.
---

# add-venue

把一個新場次收進語料庫。**這個 skill 的產出會被別人當成權威來用**，所以寧可標「查過，沒有」也不要憑印象填。

## Step 1 — 找到一手來源（不要只找一頁）

投稿須知**通常散在多個頁面**。已知的分佈樣態：

| 場次類型 | 典型分佈 |
|---|---|
| 期刊 | 期刊首頁（metrics、範圍）+ submit 頁（規定本體）+ 外部標準頁（JARS/TOP） |
| 研討會 | 學會年會通則頁（不變的部分）+ 該年度頁（日期地點）+ Presenter Information 子頁（投稿規定）+ 投稿系統（Ex Ordo/EasyChair） |

**URL 不可推測。** 實測過的陷阱：APA 的 `/submission-guidelines` 是 404、真路徑 `/submit`；Psychometric Society 的 `/imps` 是 404、真路徑帶年份 `/imps-2026`。找不到就從首頁導覽點進去，把真實 URL 記下來。

## Step 2 — 測試抓取方式，記進 `fetch.method`

```bash
curl -sS -L --max-time 15 -w '\n%{http_code}|%{size_download}' "<url>" | tail -1
```

判讀：

- 正常大小、狀態 200 → `method: http`, `http_viable: true`
- **200 但只有幾百 bytes** → **bot 挑戰頁**（APA 的 Incapsula 即如此）。`method: webfetch`, `http_viable: false`，並把失敗樣態寫進 `http_failure_mode`
- 403 → 同上，可能需要 `method: browser`（safari-browser）
- 多個不同 URL 回**相同大小/hash** → 決定性證據，全部是同一個挑戰頁

抓不到的頁面用 WebFetch；WebFetch 也不行才用 safari-browser。

## Step 3 — 設定 `fetch.validity`（**不可省略**）

```yaml
validity:
  must_contain: "<該頁獨有、規定改版也不會消失的字串>"
  min_extracted_chars: <保守下限>
```

**兩個條件缺一不可。** 實測：psychometricsociety.org 的 404 頁面有 28 KB，比某些真實頁面還大——單靠長度擋不住。而缺少斷言時，freshness 檢查會把空殼當內容存下，且空殼 hash 穩定不變，於是**永遠回報「沒變動」而實際上什麼都沒監看**。

`must_contain` 選字原則：挑內容性的字（如場地名、規定用語），不要挑導覽列或頁尾——那些在錯誤頁上也會出現。

## Step 4 — 填記錄

從既有樣本複製起手最快：

```bash
ls ${CLAUDE_PLUGIN_ROOT}/venues/*/          # apa/psychological-methods.yaml（期刊）
                                            # psychometric-society/imps.yaml（研討會）
```

### 三條填寫紀律

1. **查過但官網沒有 → 寫 `{status: not_published, checked: <date>}`**，不要留空。留空會讓後人以為是漏抓，於是重複去查一次不存在的東西。
   - `not_published` 官方未公布 ／ `not_found` 找不到 ／ `not_applicable` 不適用
2. **`requirements`（慢）與 `cycle`（快）分開放。** 期刊多為 `cycle.applies_to: null`；研討會反過來——requirements 薄、cycle 厚。放錯格會導致「須知是對的但截稿日是去年」。
3. **`extracted_sha256` 留 `null`**，交給 `verify.py` 建基準。不要手算——hash 必須由同一個 extractor 產生才可比。

## Step 5 — 驗證（兩支都要跑）

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py    # schema + 5 條 lint
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify.py <venue-id>   # 建 hash 基準
```

`validate.py` 的錯誤代碼：

| 代碼 | 意義 |
|---|---|
| L1 | `last_verified_at` 早於 `fetched_at` |
| L2 | 跨 source 的 hash 相同 → **抓取故障**，不是巧合 |
| L3 | `http_viable: false` 卻宣告 `method: http` |
| L4 | authoritative 來源缺 `fetch.validity` |
| W1 | 研討會 cycle 已過期（警告，非錯誤——辦完了是合法狀態） |
| W2 | 快照超過一年未驗證 |

**錯誤要修到零；警告要讀懂再決定。**

## Step 6 — 更新既有記錄（`verify.py` 回報 CHANGED 時）

1. 重新擷取該來源
2. **人工覆核差異**——找出哪些欄位真的變了。不要整份覆蓋，那會弄丟先前查證過的 `not_published` 標記
3. 更新變動欄位 + `fetched_at`
4. 重跑 `verify.py` 建新基準

改版通常只動少數欄位。整份重寫比逐欄比對更容易出錯，也丟掉累積的查證成果。
