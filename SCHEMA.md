# research-submission — Schema 設計草案 v1

> 草案日期 2026-08-03。單一樣本：*Psychological Methods*（APA）。
> 形式規格見 [`schema/venue.schema.json`](plugins/research-submission/schema/venue.schema.json)，實例見 [`venues/apa/psychological-methods.yaml`](plugins/research-submission/venues/apa/psychological-methods.yaml)。

---

## 這個專案跟 livedocs 的關係

繼承**哲學**（primary-source-first、不維護會腐爛的二手索引、provenance 一律露出），但**機制相反**：

| | livedocs | research-submission |
|---|---|---|
| 底層變動速度 | 快（套件版本天天動） | **慢**（投稿須知數年不變） |
| 一手來源可機讀？ | 是（實測 25 個 docs host，約 88% 有 `llms.txt`） | **否**（實測 6 家出版社，`llms.txt` 0/6） |
| 因此的策略 | **不存**，每次現查 | **存**，語料庫就是產品 |
| 「live」的意義 | 即時取得最新版 | **驗證存下來的還算不算數** |
| 覆蓋策略 | 全域解析 | **需求驅動**（有人要投才加） |

換句話說：livedocs 不能存，因為存了就過時；這個必須存，因為底層本來就慢，而且抓取成本高（見下）。

---

## 三個驅動設計的實測發現

全部來自 2026-08-03 對 APA 的實際探測，都不是憑空推想得到的。

### 1. 一手來源不可機讀，而且半數擋 bot

`llms.txt` 探測結果：

| Host | 結果 |
|---|---|
| www.apa.org | 404 |
| www.elsevier.com | 404 |
| link.springer.com | 404 |
| onlinelibrary.wiley.com | **403** |
| journals.sagepub.com | **403** |
| www.tandfonline.com | **403** |

→ 沒有 llms.txt 這層基礎，所以必須 **per-publisher adapter**（分解軸是出版社，不是期刊）。

### 2. 抓取會安靜地失敗 —— 這條決定了 schema 的形狀

對 APA 三個頁面做一般 HTTP 抓取：

```
200      212 bytes  sha256:8bd329e5869bd8e0  /pubs/journals/met/submit
200      212 bytes  sha256:8bd329e5869bd8e0  /pubs/journals/met
200      212 bytes  sha256:8bd329e5869bd8e0  apastyle.apa.org/jars/quantitative
```

三個不同頁面回**同一個 hash**，內容是 Incapsula bot 挑戰頁，狀態碼是 **200 而非 403**。

**後果**：天真的 `content_hash` 比對會永遠回報「沒變動、仍然新鮮」，但它監看的是一個空殼。**這比沒有 freshness 檢查更危險**，因為它製造虛假信心 —— 而這個工具最該防止的傷害，正是有人照著過期的字數上限寫完一整篇稿。

→ Schema 強制三件事：
- `snapshot.extracted_sha256` 算在**抽取後的純文字**上，不是 HTTP response body
- 每個 source 必須有 `fetch.validity`（`must_contain` + `min_extracted_chars`），抓取後先斷言再入庫
- 跨 source 的 hash 相同 → 視為**故障**，不是巧合

### 3. 須知是散的，而且路徑會騙人

*Psychological Methods* 的須知分佈在**三個頁面**：期刊首頁、`/submit`、以及 apastyle 網域的 JARS。

而且 `/pubs/journals/met/submission-guidelines`（最直覺的路徑）是 **404**，真正的路徑是 `/submit`。

→ `sources` 必須是**列表**且每個帶 `role`；per-publisher 的 URL 慣例必須被編碼，不能靠猜。

---

## 讀取用快照，live 用於驗證

**不採用 live-every-time。** 理由是上面第 2 點的直接推論：APA 的 bot 挑戰回 200 而非 403，若設計成每次現查且不存底，抓取退化時工具**沒有東西可退回**，還可能把空殼當權威呈現。有快照則優雅降級（「現查失敗，以下是 N 天前的快照」）。加上須知數年不變、抓取需要瀏覽器層工具，live-every-time 是高成本換無收益。

### 時間戳記要三個，不是一個

單一時間戳記只表達「我何時看過」，不表達「現在是否仍為真」。兩筆同樣標 2026-08-03 的記錄，一筆來源至今未動、一筆昨天改版 —— 可信度完全不同。

| 欄位 | 意義 |
|---|---|
| `fetched_at` | 內容擷取時間 |
| `last_verified_at` | 最後一次重抓並確認 hash 相同的時間 |
| `extracted_sha256` | 當時看到的內容指紋 |

**staleness = `now − last_verified_at`**，不是 `now − fetched_at`。2020 年抓、上週驗證過沒變 → 新鮮；上個月抓、之後沒驗證 → 不確定。單一時間戳無法區分這兩者。

驗證發現 hash 不同 → 重新擷取，`fetched_at` 才更新。

### 兩種使用情境，兩種嚴格度

| 情境 | 政策 |
|---|---|
| 瀏覽／跨場次比較（「A 和 B 哪個字數寬」） | 讀快照。快、可離線 |
| 選期刊（`choose-venue`） | 排序讀快照；回報淘汰前、開始為第一志願改稿前現場驗證 |
| **實際準備投稿** | **強制現場驗證**；記錄過期不得靜默通過 |

理由：投稿前是唯一「錯了會很貴」的時刻。平常寬鬆、關鍵時刻嚴格，優於一律嚴格（難用）或一律寬鬆（危險）。

這也是名稱裡 `live` 的正當性所在 —— live 用在驗證，不在讀取。

---

## 四個 schema 決策

### A. `requirements` / `cycle` 二分 —— 更新頻率不同的東西不能放同一格

| 欄位群 | 變動 | 適用 |
|---|---|---|
| `requirements` | 慢（數年） | 期刊 + 研討會 |
| `cycle` | **每年** | 研討會為主（截稿日、投稿窗口、當屆主題） |

研討會的須知本體穩定，但**日期每年翻新**，而日期錯了是致命的。混在一起用同一個更新頻率處理，遲早出現「須知對、截稿日是去年」這種最糟組合。

`cycle` 帶 `applies_to` 與 `expires_at`；過期時工具**必須主動示警**，不得靜默沿用。

### B. `unknown` 是一級公民 —— 分辨「查過沒有」與「還沒查」

APA 官網**不公布**接受率與審稿時程。留空會讓後人以為是漏抓，於是重複去查一次不存在的東西。

所以任何純量欄位都可以改寫成：

```yaml
acceptance_rate:
  status: not_published     # not_published | not_found | not_applicable
  checked: 2026-08-03
  src: journal_home
```

- `not_published` —— 查了，官方沒公布
- `not_found` —— 查了，找不到（可能存在於別處）
- `not_applicable` —— 對這個場次不適用

### C. 長度要保留原生單位，不要假裝可比

APA 寫的是「**50 頁雙倍行距、12pt Times New Roman、含參考文獻/表/圖/附錄**」。這不等於任何確定的字數。硬轉成字數再拿去跨期刊比較，是製造假精確。

```yaml
length:
  value: 50
  unit: pages_double_spaced
  basis: {font: Times New Roman, size_pt: 12, spacing: double}
  includes: [references, tables, figures, appendixes]
  approx_words: {value: 12500, assumption: "250 words/page", confidence: low}
  exceptions: "只有被判定能做出 exceptional contribution 才考慮超長"
```

`approx_words` 是選配且**必須標註換算假設與信心**，讓比較功能可用但不騙人。

### D. 條件式要求要能表達 —— 不是所有規定都無條件適用

遮蔽審查是選配，但**一旦選了就帶出一整串額外規定**（清掉補助案號、IRB 機構名、自我引用、repository 連結）。攤平成無條件清單會誤導。

```yaml
conditional:
  - id: masked_review
    optional: true
    when: "作者於投稿時主動要求"
    requirements: [...]
```

### E. 外部標準要能表達「不適用」

JARS 對本領域有真實缺口：apastyle 的 quantitative 頁面**沒有**針對模擬研究、提出新估計式的方法論文、或既有資料二次分析的模組。

```yaml
standards:
  - id: jars-quant
    applicability:
      - {case: structural_equation_modeling, status: covered, ref: quant-table-7.pdf}
      - {case: monte_carlo_simulation, status: no_module}
      - {case: new_estimator_development, status: no_module,
         note: "Analytic methods 表是給『應用』既有技術的實證研究"}
    escalation: styleexpert@apa.org
```

---

## 研討會樣本帶來的修正（2026-08-03 稍後）

用 IMPS 實跑後，證實並修正了幾點：

### 不對稱得到證實，但方向比預期更極端

| | 期刊（Psychological Methods） | 研討會（IMPS） |
|---|---|---|
| `requirements` | **厚** —— 篇幅、雙摘要、格式、TOP、JARS、CRediT… | **薄** —— 學會層級只有通則；投稿類型/字數/格式官網**均未載明** |
| `cycle` | 空（`applies_to: null`） | **厚** —— 日期、地點、報名窗口、投稿系統 |

研討會的具體投稿規定散在各年度的 Presenter Information 子頁，學會層級查不到。所以 `requirements` 薄**不代表沒有規定**，記錄裡必須用 `not_found` 明講，否則會被誤讀成「沒限制」。

### 新增 `cycle.status`

僅靠日期比較無法區分兩種狀態：**「截稿已過但還能報名參加」** vs **「整場已經辦完」**。後者的地點與日期完全不可沿用。故加 `status: upcoming | submissions_open | submissions_closed | held`。

### 過期是警告，不是錯誤

初版把 cycle 過期做成 error，結果 IMPS 2026（7/24 結束）讓語料庫永遠紅燈。**辦完了是合法狀態，不是缺陷。** 改成 W1 警告；若當成 error，人會停止閱讀驗證輸出，真正的錯誤反而被淹沒。

### `must_contain` 是必要條件，不是備援

實測 psychometricsociety.org 的 **404 頁面有 28 KB**，比某些真實頁面還大 —— 單靠 `min_extracted_chars` 擋不住。兩個斷言缺一不可。

### `fetch.method` 確實需要 per-source

同一批探測中，Psychometric Society 一般 HTTP 就抓得到（37/55 KB、hash 各異），APA 則被 Incapsula 擋。兩者無法用同一種方式處理。

---

## 尚未決定的事

誠實列出，避免看起來比實際成熟：

1. ~~`kind: conference` 的樣本~~ → **已做**（`psychometric-society/imps`），並回頭修正了 schema（見上節）。
2. ~~抽取層沒定義~~ → **已定**：`verify.py` 用標準庫的 `stdlib-htmlparser/1`，並在 `snapshot.extractor` 記版本（hash 只在同一 extractor 內可比）。**但既有記錄的 `extracted_sha256` 仍為 `null`** —— 基準要等 `verify.py --write` 覆核後才寫入。
3. **plugin 顆粒度**仍未定案。v0.1 是**單一 plugin 裝所有場次**（最簡單、可先用）。若語料庫長大到跨領域，再拆 per-family（`apa-journals` / `psychometrics-conferences`）。拆分點應由實際使用觸發，不預先切。
4. ~~是否需要 MCP server~~ → **v0.1 不做**。操作只是「讀 YAML + 重抓比對」，skill + script 就夠；livedocs 需要 Swift MCP 是因為它做即時多路由解析，本專案沒有那個需求。若之後要跨場次結構化查詢（「所有字數上限 < 8000 的心理計量期刊」）再評估。
5. **未驗證的假設**：`must_contain` 選字的長期穩定性。目前挑的是內容性字串（場地名、規定用語），但期刊改版時這些字可能消失，導致 `INVALID` 誤報。要累積幾次真實改版才知道誤報率。
