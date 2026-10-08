#!/usr/bin/env python3
"""一本期刊實際刊了什麼：用 OpenAlex 掃標題，回答「這個主題它收不收、收的時候怎麼包裝」。

choose-venue 的分工：期刊**明文排除**什麼，以官方文字為準（choose-venue Step 2）；
一個主題它**實際收多少、用什麼框架收**，以本工具掃到的刊出論文為準（Step 3）。
範圍描述回答不了後者——它說「不限領域」時，刊出的論文仍可能只用特定框架收某個主題。

用法:
  python3 scripts/venue_topic_scan.py --venue biometrika-trust/biometrika --term "mixture model"
  python3 scripts/venue_topic_scan.py --venue asa/jasa --term "latent class" --term "finite mixture"
  python3 scripts/venue_topic_scan.py --issn 0006-3444 --term identifiability --pair 'estimat\\w*'
  python3 scripts/venue_topic_scan.py --venue ims/annals-of-statistics --term "finite mixture" --json

  --term   可重複。多字詞預設當**片語**查（加引號）；--loose 改成「各字都出現即可」。
           OpenAlex 的 title.search 會做一些字形正規化（例如 model 通常也命中 models），
           但規則不公開；要確定涵蓋某個字形，就把它另下一個 term。
  --pair   可重複。**不分大小寫的正則表達式**，在每個 term 的結果標題裡數命中篇數
           （看主題通常和什麼一起出現）。要涵蓋字形變化自己寫，例如 'estimat\\w*'。
  --since / --until  出版年範圍（含端點；只給一端也可以）。建議先不加，看全部年代的趨勢。
  --examples  每個 term 列出幾篇最近的例子（預設 8）

輸出的限制，要連同數字一起告訴使用者：只掃標題；同義詞要自己多下 term；
只算 OpenAlex 認定的 primary_location（首要刊載處）是這本期刊的論文，期刊歸屬偶有錯置；
超過 MAX_RECORDS 時年代分布只算抓到的那些。

設定 OPENALEX_MAILTO=<email> 可進 OpenAlex 的 polite pool（較穩定）；不設也能用。
需要 pyyaml（讀 venue 記錄）與網路。
"""
import argparse
import collections
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.openalex.org"
MAX_RECORDS = 1000
ISSN_RE = re.compile(r"^[0-9]{4}-[0-9]{3}[0-9X]$")


def issn_from_venue(venue_id):
    import yaml
    path = ROOT / "venues" / f"{venue_id}.yaml"
    if not path.exists():
        sys.exit(f"找不到 venue 記錄 {path}（先用 add-venue 收錄，或改用 --issn）")
    rec = yaml.safe_load(path.read_text())
    ident = rec.get("identity") or {}
    cands = []
    oa = (ident.get("external_ids") or {}).get("openalex")      # 人工設定的優先
    if isinstance(oa, str) and oa.startswith("issn:"):
        cands.append(oa.split(":", 1)[1])
    issn = ident.get("issn") or {}
    if isinstance(issn, dict):
        for k in ("print", "electronic"):
            v = issn.get(k)
            if isinstance(v, str):
                cands.append(v)
    cands = [c for c in cands if ISSN_RE.match(c)]
    if not cands:
        sys.exit(f"{venue_id} 的記錄裡沒有可用的 ISSN（external_ids.openalex / identity.issn）；改用 --issn")
    return list(dict.fromkeys(cands)), ident.get("name", venue_id)


def get(path, params):
    mailto = os.environ.get("OPENALEX_MAILTO")
    if mailto:
        params = {**params, "mailto": mailto}
    url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "research-submission/venue_topic_scan"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt * 2)
                continue
            raise


def resolve_source(cands):
    """ISSN 對不到 OpenAlex 的期刊時，每個 term 都會回 0，看起來像「這本不收」。
    依序試每個候選 ISSN，用第一個對得上的；全部對不上就停下來，不回報零篇。"""
    for issn in cands:
        srcs = get("sources", {"filter": f"issn:{issn}", "per_page": 5}).get("results", [])
        if srcs:
            return issn, [s.get("display_name") or "?" for s in srcs]
    sys.exit(f"✗ OpenAlex 找不到 ISSN {'、'.join(cands)} 對應的期刊——不是「零篇」，是查不到期刊。檢查 ISSN 或改用另一個。")


def scan(issn, term, since, until, loose):
    q = term if (loose or " " not in term) else f'"{term}"'
    flt = [f"primary_location.source.issn:{issn}", f"title.search:{q}"]
    if since or until:
        flt.append(f"publication_year:{since or ''}-{until or ''}")
    params = {"filter": ",".join(flt), "per_page": 200, "sort": "publication_year:desc", "cursor": "*"}
    works, total = [], None
    while params.get("cursor") and len(works) < MAX_RECORDS:
        d = get("works", params)
        if total is None:
            total = (d.get("meta") or {}).get("count")
            if not isinstance(total, int):
                raise RuntimeError(f"OpenAlex 回應缺少 meta.count（term {term!r}）——無法得知總篇數，不當成 0")
        works.extend(d.get("results", []))
        params["cursor"] = d.get("meta", {}).get("next_cursor")
        if not d.get("results"):
            break
    return total, works


def summarize(term, total, works, pairs, n_examples):
    decades = collections.Counter((w.get("publication_year") or 0) // 10 * 10 for w in works)
    out = {"term": term, "count": total, "retrieved": len(works),
           "by_decade": {f"{k}s": v for k, v in sorted(decades.items()) if k},
           "by_decade_truncated": len(works) < total, "pairs": {}, "examples": []}
    for p in pairs:
        rx = re.compile(p, re.IGNORECASE)
        hit = [w for w in works if rx.search(w.get("title") or "")]
        out["pairs"][p] = {"with": len(hit), "of": len(works)}
    for w in works[:n_examples]:
        authors = [(a.get("author") or {}).get("display_name") or "?" for a in w.get("authorships", [])[:3]]
        out["examples"].append({"year": w.get("publication_year"), "title": w.get("title"),
                                "authors": authors, "doi": w.get("doi")})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--venue", help="venue id，例 biometrika-trust/biometrika")
    src.add_argument("--issn")
    ap.add_argument("--term", action="append", required=True)
    ap.add_argument("--pair", action="append", default=[])
    ap.add_argument("--loose", action="store_true", help="多字詞不當片語，各字都出現即可")
    ap.add_argument("--since", type=int)
    ap.add_argument("--until", type=int)
    ap.add_argument("--examples", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    for t in a.term:
        if any(c in t for c in ',"|'):
            sys.exit(f"✗ term 不可含逗號、雙引號或 |：{t!r}（會弄壞 OpenAlex 的 filter）")
    for p in a.pair:
        try:
            re.compile(p)
        except re.error as e:
            sys.exit(f"✗ --pair 不是合法的正則表達式：{p!r}（{e}）")

    if a.venue:
        cands, name = issn_from_venue(a.venue)
    else:
        if not ISSN_RE.match(a.issn):
            sys.exit(f"✗ ISSN 形狀不對：{a.issn!r}")
        cands, name = [a.issn], a.issn

    try:
        issn, oa_names = resolve_source(cands)
        results = []
        for term in a.term:
            total, works = scan(issn, term, a.since, a.until, a.loose)
            results.append(summarize(term, total, works, a.pair, a.examples))
    except (urllib.error.URLError, TimeoutError, RuntimeError) as e:
        print(f"✗ OpenAlex 查詢失敗：{e}", file=sys.stderr)
        return 1

    report = {"venue": name, "issn": issn, "openalex_source": oa_names, "queried": time.strftime("%Y-%m-%d"),
              "since": a.since, "until": a.until, "phrase": not a.loose, "results": results,
              "caveats": ["只掃標題", "同義詞需自行另下 term", "只算 primary_location 是本刊的論文；OpenAlex 期刊歸屬偶有錯置",
                          "多字詞" + ("各字都出現即算" if a.loose else "以片語比對")]}
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    span = f"{a.since or '…'}–{a.until or '…'}" if (a.since or a.until) else "全部年份"
    mode = "寬鬆計法（多字詞各字出現即算）" if a.loose else "片語計法"
    print(f"{name}（ISSN {issn}；OpenAlex：{'、'.join(oa_names)}；{span}；{mode}；查詢日 {report['queried']}）")
    for r in results:
        print(f"\n■ 標題含「{r['term']}」{'（各字）' if a.loose and ' ' in r['term'] else ''}：{r['count']} 篇")
        if r["by_decade"]:
            note = f"（只算抓到的最近 {r['retrieved']} 筆）" if r["by_decade_truncated"] else ""
            print("  依年代：" + "、".join(f"{k} {v}" for k, v in r["by_decade"].items()) + note)
        for p, c in r["pairs"].items():
            print(f"  其中標題也符合 /{p}/：{c['with']}/{c['of']}")
        for e in r["examples"]:
            print(f"  {e['year']} | {e['title']} | {', '.join(e['authors'])}")
    print(f"\n限制：只掃標題；{mode}，與另一種計法的數字不可混用；同義詞要另下 term；"
          "只算 primary_location 是本刊的論文，OpenAlex 的期刊歸屬偶有錯置。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
