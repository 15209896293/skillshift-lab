# P0-A Public Source Candidate Task Inventory

## Status

Draft public-source seed inventory.

These are candidate traditional training task patterns gathered from public web-searchable materials and common Big Data Technology curriculum structure.

They are not yet confirmed as local school historical tasks.

## Inventory

| Task ID | Candidate Task | Skill Area | Traditional Expected Output | Likely Agent Impact | Audit Priority | Source Basis |
| --- | --- | --- | --- | --- | --- | --- |
| P0A-PUB-001 | MySQL database creation, table design, data import, and basic query | SQL / MySQL | database schema, imported data, query results | Agent can likely generate SQL quickly, but may make schema or encoding mistakes | High | SRC-PUB-003 |
| P0A-PUB-002 | SQL aggregation and abnormal result diagnosis | SQL / MySQL | correct aggregate query and explanation | Agent may produce runnable but logically wrong queries; strong verifier potential | High | SRC-PUB-003 |
| P0A-PUB-003 | Linux environment setup for big data tools | Linux | installed packages, configured users, environment variables | Agent can provide commands but may assume wrong OS/version/path | High | SRC-PUB-004 |
| P0A-PUB-004 | Linux service fault diagnosis and recovery | Linux / Ops | service restored, logs checked, configuration fixed | Agent can suggest likely fixes but verification and log interpretation remain important | High | SRC-PUB-004 |
| P0A-PUB-005 | HDFS basic command operation and file management | Hadoop / HDFS | directories, uploaded files, command outputs | Agent can list commands; real environment state still needs verifier | Medium | SRC-PUB-005 |
| P0A-PUB-006 | Hadoop pseudo-distributed environment setup | Hadoop | running NameNode/DataNode, web UI, sample job | Agent may hallucinate version-specific config; environment friction likely high | Medium | SRC-PUB-005 |
| P0A-PUB-007 | Spark word count or simple ETL task | Spark | Spark job result and output file | Agent can generate code; dependency and runtime issues likely expose real skill | Medium | SRC-PUB-002 |
| P0A-PUB-008 | Python CSV cleaning with missing values and type conversion | Python / Data Cleaning | cleaned CSV, summary statistics | Agent can code quickly; hidden edge cases make this strong dual-track candidate | High | SRC-PUB-006 |
| P0A-PUB-009 | Multi-source data merge and consistency check | Python / SQL | merged dataset, deduplication, quality report | Agent may miss key constraints or duplicate rules; strong evidence contract candidate | High | SRC-PUB-006 |
| P0A-PUB-010 | User behavior analysis pipeline from raw logs to summary indicators | Big Data / Analytics | processed indicators, charts or tables | Agent can draft pipeline but may mishandle fields, time windows, or metrics | High | SRC-PUB-001 |
| P0A-PUB-011 | Data visualization dashboard or chart report | Visualization | charts, labels, explanatory report | Agent can produce chart code; interpretation and data correctness need checking | Medium | SRC-PUB-001 |
| P0A-PUB-012 | Simple crawler or API data acquisition task | Python / Data Acquisition | collected dataset, saved file, basic cleaning | Agent can generate code but may break on network, anti-crawl, encoding, schema drift | Medium | Common public curriculum pattern |

## Initial Priority Recommendation

Start with these five because they are easier to verify and fit the first SQL/MySQL vertical slice direction:

1. P0A-PUB-001 MySQL database creation and import.
2. P0A-PUB-002 SQL aggregation and abnormal result diagnosis.
3. P0A-PUB-008 Python CSV cleaning.
4. P0A-PUB-009 Multi-source data merge and consistency check.
5. P0A-PUB-010 User behavior analysis pipeline.

## What Still Needs Human Confirmation

For each candidate, the product owner should later confirm whether there is a real local task, screenshot, assignment sheet, Word document, textbook exercise, or teacher-provided version.

Until then, mark each task as:

`public-source candidate`

not:

`real local historical task`
