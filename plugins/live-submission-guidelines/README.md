# live-submission-guidelines (plugin)

學術投稿須知的一手來源語料庫。完整說明見 [repo README](https://github.com/PsychQuant/live-submission-guidelines)。

## Skills

| Skill | 何時觸發 |
|---|---|
| `submission-guidelines` | 查詢/比較投稿規定、對照稿件、投稿前驗證 |
| `venue-add` | 場次尚未收錄，或 `verify.py` 回報來源已變動 |

## Scripts

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py            # schema + 4 錯誤 / 2 警告 lint
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify.py <venue-id>   # 重抓、斷言、比對 hash
```

## Layout

```
venues/<publisher>/<venue>.yaml   # 語料庫
schema/venue.schema.json          # 形式契約
scripts/{validate,verify}.py
```

依賴：`pyyaml`、`jsonschema`（validate.py）；`verify.py` 只用標準庫。
