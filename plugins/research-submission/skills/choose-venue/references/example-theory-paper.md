# 精簡範例：一篇理論稿件的選刊

虛構化範例：稿件主題是虛構的（某潛在類別／有限混合模型的識別理論），期刊事實與掃描數字是 2026-10-08 實際查到的值。
本範例只示範 Step 2、3、3.5、5 的判讀；完整輸出還要有比較表、補強清單與 `not_published` 欄位（見 SKILL.md〈輸出格式〉）。
引用期刊事實前，照 SKILL.md Step 1 的 (a)(b) 現場驗證。

## 稿件側寫（虛構）

| 項目 | 內容 |
|---|---|
| 貢獻類型 | 理論為主（識別定理），附一個決定類別數的程序 |
| 稿件現況 | 有證明；只用一個經典資料示範（示範用，不是驅動研究的應用）；模擬很少 |
| 必須條件 | 無 |
| 偏好 | 希望統計界認可 |

## Step 1 — 候選

`asa/jasa`、`rss/jrss-series-b`、`rss/jrss-series-c`、`biometrika-trust/biometrika`、`ims/annals-of-statistics`（family `statistics-journals`），加上相鄰的 `psychometric-society/psychometrika`（`psychometrics-journals`；判斷：潛在類別模型是心理計量的核心主題）。沒選 `apa-journals`（Psychological Methods）與各 `*-conferences`（判斷：前者偏方法應用與教學，後者不是期刊）。

## Step 2 — 淘汰

全部 `last_verified_at` 2026-10-08。

| 期刊 | 結果 | 依據 |
|---|---|---|
| JRSS-C | 淘汰（第 1 類） | 「Methodological papers that are not motivated by a genuine application are not acceptable」（`oup_instructions`）。判斷對象是定位：這是方法論文，不是由應用驅動 |
| JASA | 保留；進 Step 4 | 「more narrowly focused contributions, while of considerable merit in their own right, may be inappropriate for the Theory and Methods section」（`tf_instructions`）——保留語氣 |
| JRSS-B | 保留；進 Step 4 | 篇幅：「Please strive to keep the paper under 30 pages」（`general_instructions`），含附錄 |
| Biometrika | 保留；進 Step 4 | 「Papers concerned purely with sampling properties of existing procedures or minor developments thereof are typically unsuitable unless such properties reveal considerable structural understanding」（`about`）——保留語氣 |
| Annals | 保留；進 Step 4 | 「Papers ... with a focus on technical improvements are discouraged, regardless of mathematical depth, unless they are substantial and clearly consequential for the field of statistics」（`ae_guidelines`）——保留語氣。同一準則給副編輯的**預期** desk-reject 比例約 30% 與 20%，不是錄取率，不可換算 |
| Psychometrika | 保留；進 Step 4 | 官方原文「likely to be assigned a lower priority ... (unless the manuscript has important implications for the field)」（`preparing`）——保留語氣 |

## Step 3 — 主題證據

片語計法、標題、全部年份，查詢日 2026-10-08（括號內為 2010、2020 年代篇數）；同義詞未窮舉：

| 期刊 | mixture model | latent class | identifiability |
|---|---|---|---|
| JASA | 55（14、12） | 21（4、1） | 21（3、4） |
| JRSS-B | 21（3、6） | 1（0、1） | 3（0、2） |
| Biometrika | 20（2、2） | 4（0、0） | 14（3、1） |
| Annals | 23（4、8） | 3（1、2） | 17（6、5） |
| Psychometrika | 14（4、7） | 50（10、10） | 34（6、13） |

判讀（判斷）：

- 「latent class」在 Biometrika 的 4 篇全在 1980 年代——年代趨勢比總數有用，這個主題在那裡要換框架（例如改用 mixture／identifiability 的語言）。
- Biometrika 的 identifiability 2010 年以來只有 4 篇，個位數不下結論；全部年份 14 篇，其中標題符合 `/estimat\w*/` 的只有 2 篇，純識別性論文並不罕見。

## Step 3.5 — 最接近的前人結果（條件式示範）

把核心主張寫成一句可檢驗的話，找出最接近的二到五篇、讀原文後逐篇寫出它證了什麼與前提。
**若**比對發現核心主張的主要情形已有前人結果，推薦就改為「先重新定位，再排序」，並在定理層次寫出差異；
**若**沒有，照 Step 5 排序。不論哪一種，查證過的文獻都交給文獻庫歸檔。

## Step 5 — 推薦怎麼隨前提翻轉

每一列都從 Step 2 重跑；Step 3.5 應在排序之前做完，表中各列都假設它的結論是「沒有被涵蓋」。

| 前提 | 推薦 | 理由 |
|---|---|---|
| 沒有驅動研究的應用、模擬很少 | Biometrika → Psychometrika | Biometrika 看概念新穎（判斷）；JASA 要求「The research reported should be motivated by a scientific or practical problem」（`tf_instructions`） |
| 補得出驅動研究的應用與模擬 | JASA → Biometrika → Psychometrika | JASA 的主要門檻消失；正文 35 頁、證明移到補充材料（`tf_instructions`；同一記錄另有「平均約 30 頁含附錄」的說法，兩者不一致）。JRSS-C 仍淘汰：補資料不改變這是方法論文的定位 |
| 掃描顯示主題在篇幅較短的那本也有先例 | Biometrika → JASA → Psychometrika | 短版先寫、被拒再擴寫成長版比反向容易（判斷） |

保留但沒排進順序（判斷；理由都不是 Step 2 或原則一已排除的那幾種）：

- **JRSS-B**：30 頁含附錄（`general_instructions`），證明多的稿件要大幅刪減。**排入條件**：證明能壓進 30 頁內，或改寫成方法為主、證明為輔。
- **Annals**：要說明「substantial and clearly consequential for the field of statistics」（`ae_guidelines`），也要在 cover letter 寫出 key innovations（`ae_guidelines`）。**排入條件**：重新定位後能具體說明對統計的廣泛影響。

首次決定時間沒有拿來排序：JASA 是平均 63 天（`tf_about`），Biometrika 是「Nearly 75% ... within one month」（`publishing`，未載統計期間），不是同一種統計量；其餘三本未公布。

## 學到的事

1. 主題契合以刊出的論文為準，明文排除以官方文字為準；範圍說「不限領域」不等於每個框架都受歡迎。
2. 年代趨勢比總數有用；個位數樣本不下結論；片語計法與寬鬆計法的數字不可混用。
3. 選刊之前先比對最接近的前人結果；它可能改變的是稿件定位，影響比選哪本期刊更大。
