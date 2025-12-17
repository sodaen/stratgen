# STRATGEN SYSTEM-ANALYSE
# Erstellt: Mi 17. Dez 17:02:44 CET 2025

## 1. VERZEICHNISSTRUKTUR
```
.
./Acme GmbH (2)
./Acme GmbH (2)/docProps
./Acme GmbH (2)/ppt
./Acme GmbH (2)/ppt/printerSettings
./Acme GmbH (2)/ppt/_rels
./Acme GmbH (2)/ppt/slideLayouts
./Acme GmbH (2)/ppt/slideLayouts/_rels
./Acme GmbH (2)/ppt/slideMasters
./Acme GmbH (2)/ppt/slideMasters/_rels
./Acme GmbH (2)/ppt/slides
./Acme GmbH (2)/ppt/slides/_rels
./Acme GmbH (2)/ppt/theme
./Acme GmbH (2)/_rels
./.aider.tags.cache.v4
./.aider.tags.cache.v4/83
./.aider.tags.cache.v4/83/cc
./.aider.tags.cache.v4/d8
./.aider.tags.cache.v4/d8/0f
./.aider.tags.cache.v4/e2
./.aider.tags.cache.v4/e2/10
./assets
./assets/templates
./assets_tmp
./backend
./backend/middleware
./backend/__pycache__
./backend/routers
./backend/schemas
./backend/.venv
./backend/.venv/bin
./backend/.venv/include
./backend/.venv/include/python3.12
./backend/.venv/lib
./backend/.venv/lib/python3.12
./backend/.venv/lib/python3.12/site-packages
./backend/.venv/lib/python3.12/site-packages/annotated_doc
./backend/.venv/lib/python3.12/site-packages/annotated_doc-0.0.3.dist-info
./backend/.venv/lib/python3.12/site-packages/annotated_doc-0.0.3.dist-info/licenses
./backend/.venv/lib/python3.12/site-packages/annotated_types
./backend/.venv/lib/python3.12/site-packages/annotated_types-0.7.0.dist-info
./backend/.venv/lib/python3.12/site-packages/annotated_types-0.7.0.dist-info/licenses
./backend/.venv/lib/python3.12/site-packages/anyio
./backend/.venv/lib/python3.12/site-packages/anyio-4.11.0.dist-info
./backend/.venv/lib/python3.12/site-packages/anyio-4.11.0.dist-info/licenses
./backend/.venv/lib/python3.12/site-packages/anyio/abc
./backend/.venv/lib/python3.12/site-packages/anyio/_backends
./backend/.venv/lib/python3.12/site-packages/anyio/_core
./backend/.venv/lib/python3.12/site-packages/anyio/streams
./backend/.venv/lib/python3.12/site-packages/click
```

## 2. SERVICES (109 Dateien)
```
services/agent_playbook.py              2006
services/agent.py                       3810
services/agent_runner.py                3963
services/argument_engine.py             16405
services/asset_resolver.py              5720
services/asset_tagger.py                18873
services/auth.py                        506
services/auto_learner.py                20921
services/brand.py                       2174
services/brand_store.py                 2164
services/brand_voice_extractor.py       18740
services/briefing_analyzer.py           18574
services/cache.py                       1185
services/cache_stub.py                  353
services/changelog.py                   337
services/changelog_rotate.py            1480
services/chart_generator.py             22170
services/chat_learner.py                4958
services/citations.py                   1109
services/compat.py                      2326
services/competitive_intelligence.py    15705
services/connectors.py                  3499
services/content_generator_v2.py        15296
services/content_intelligence.py        17915
services/critic.py                      4968
services/data_services.py               11140
services/data_sources.py                1617
services/datasources.py                 2363
services/datasource_store.py            1745
services/db.py                          10560
services/deck_builder.py                899
services/deck_filler.py                 9556
services/deck_templates.py              1608
services/ds_ingest.py                   16556
services/export_api.py                  4141
services/export_ingest.py               2842
services/export_service_v2.py           4916
services/export_tools.py                3350
services/feature_orchestrator.py        23926
services/feedback_loop.py               20613
services/generator.py                   14423
services/graph_extract.py               1719
services/hybrid_search.py               13949
services/images.py                      4046
services/image_store.py                 3722
services/ingest.py                      4816
services/__init__.py                    0
services/intelligent_deck_generator.py  26582
services/knowledge_enhanced.py          30712
services/knowledge_graph.py             1739
services/knowledge_index.py             3344
services/knowledge_metrics.py           10592
services/knowledge_pipeline.py          18711
services/knowledge.py                   32999
services/learn_engine.py                2277
services/learning_adaptation.py         25146
services/learn.py                       1058
services/learn_watcher.py               2028
services/live_generator.py              32791
services/llm_content.py                 16219
services/llm.py                         2231
services/markdown.py                    696
services/multimodal_export.py           23822
services/nlg.py                         4376
services/outline.py                     5899
services/persona_engine.py              27593
services/plan_scale.py                  3345
services/policies.py                    1239
services/ppt_renderer.py                17537
services/pptx_designer.py               14136
services/pptx_designer_v2.py            21981
services/pptx_designer_v3.py            21559
services/pptx_extract.py                2796
services/pptx_ingest.py                 7622
services/preview_image.py               2208
services/projects_store.py              1944
services/query_expander.py              6648
services/query_optimizer.py             8298
services/rag_boost.py                   1002
services/rag_pipeline.py                4230
services/reranker.py                    9560
services/rerank.py                      1092
services/research_enrichment.py         5526
services/research_providers.py          540
services/reviewer.py                    2492
services/roi_calculator.py              18706
services/self_learning.py               24743
services/semantic_slide_matcher.py      14956
services/slide_dna_analyzer.py          17794
services/slide_structure_engine.py      14947
services/sources_store.py               4849
services/source_tracker.py              5339
services/story_engine.py                23663
services/strategic_grammar.py           4044
services/style_presets.py               1217
services/style_profiler.py              2037
services/style_profiles.py              3287
services/telemetry.py                   1712
services/template_learner.py            9722
services/templates.py                   1423
services/template_tools.py              5774
services/textnorm.py                    666
services/unified_knowledge.py           11114
services/unsplash_service.py            6419
services/validation.py                  2627
services/validators.py                  6938
services/vision_analyzer.py             7100
services/visual_intelligence.py         25864
services/visuals.py                     3864
```

## 3. BACKEND/API (99 Dateien)
```
backend/admin_metrics_api.py         23638
backend/agent_autotune_api.py        2903
backend/agent_mission_api.py         670
backend/agent_review_api.py          1309
backend/agent_run_alias.py           975
backend/agent_run_v1_router.py       4656
backend/agent_state_api.py           555
backend/_agent_state.py              2449
backend/agent_v3_api.py              50179
backend/analytics_api.py             1732
backend/api_export_bridge.py         6663
backend/api.py                       29211
backend/assets_api.py                2964
backend/auth.py                      349
backend/brand_api.py                 1059
backend/brief_api.py                 1727
backend/briefs_api.py                1856
backend/competitor_api.py            1162
backend/content_api.py               3595
backend/critique_api.py              992
backend/data_services_api.py         2524
backend/datasource_api.py            14119
backend/datasources_api.py           2056
backend/db.py                        411
backend/debug_api.py                 783
backend/dev_api.py                   196
backend/enrich_api.py                2154
backend/explain_api.py               597
backend/export_api.py                4312
backend/exports_api.py               1882
backend/feedback_api.py              634
backend/files_api.py                 8033
backend/footnotes_api.py             3200
backend/generator_v2_api.py          3818
backend/graph_api.py                 758
backend/health_api.py                1482
backend/health.py                    725
backend/_http_retry.py               932
backend/image_api.py                 4453
backend/images_api.py                1754
backend/ingest_api.py                587
backend/__init__.py                  0
backend/k_control.py                 234
backend/killer_features_api.py       5084
backend/knowledge_admin_api.py       23367
backend/knowledge_analytics_api.py   27292
backend/knowledge_answer_api.py      4074
backend/knowledge_api.py             7369
backend/learn_api.py                 790
backend/live_generator_api.py        13275
backend/llm_local.py                 1379
backend/messaging_api.py             931
backend/metrics_api.py               922
backend/middleware.py                834
backend/mission_api.py               4816
backend/_mission_store.py            1253
backend/models.py                    495
backend/observability.py             3790
backend/ollama_api.py                1942
backend/ops_api.py                   2827
backend/orchestrator_api.py          6978
backend/outline_api.py               6633
backend/outline_from_content_api.py  4340
backend/persona_api.py               3978
backend/personas_api.py              669
backend/pipeline_api.py              3934
backend/planner_api.py               2989
backend/plans_api.py                 858
backend/pptx_api.py                  4359
backend/pptx_env_fallback.py         639
backend/projects_api.py              411
backend/projects_fix_api.py          3713
backend/projects_validate.py         2110
backend/providers_api.py             2726
backend/rag_alias_api.py             983
backend/rag_api.py                   7195
backend/raw_api.py                   6855
backend/research_api.py              2528
backend/roadmap_api.py               751
backend/security.py                  414
backend/sessions_api.py              9875
backend/settings_api.py              2470
backend/settings.py                  630
backend/sources_api.py               6128
backend/strategy_api.py              3903
backend/style_api.py                 629
backend/styles_api.py                812
backend/system_api.py                2396
backend/telemetry_api.py             629
backend/telemetry.py                 570
backend/template_api.py              1502
backend/templates_api.py             1292
backend/ui.py                        557
backend/unified_status_api.py        6019
backend/utils_projects.py            1926
backend/v2_shim.py                   2342
backend/versioning_api.py            1559
backend/workers_api.py               10066
backend/workers_status_api.py        601
```

## 4. FRONTEND
```
frontend/:
insgesamt 184
drwxrwxr-x   6 sodaen sodaen   4096 Dez 17 15:09 .
drwxrwxr-x  44 sodaen sodaen  28672 Dez 17 17:02 ..
drwxrwxr-x   3 sodaen sodaen   4096 Dez  6 01:06 dist
-rw-rw-r--   1 sodaen sodaen    425 Dez  1 14:37 index.html
drwxrwxr-x 143 sodaen sodaen   4096 Dez  6 00:35 node_modules
-rw-rw-r--   1 sodaen sodaen    812 Dez  6 00:35 package.json
-rw-rw-r--   1 sodaen sodaen 104210 Dez  6 00:35 package-lock.json
-rw-rw-r--   1 sodaen sodaen     80 Dez  1 14:37 postcss.config.js
drwxrwxr-x   2 sodaen sodaen   4096 Dez  1 14:42 public
drwxrwxr-x   9 sodaen sodaen   4096 Dez  4 11:37 src
-rw-rw-r--   1 sodaen sodaen    640 Dez  1 14:37 tailwind.config.js
-rw-rw-r--   1 sodaen sodaen    587 Dez  5 16:45 tsconfig.json
-rw-rw-r--   1 sodaen sodaen    213 Dez  1 14:37 tsconfig.node.json
-rw-rw-r--   1 sodaen sodaen    499 Dez  7 01:33 vite.config.ts

static/:
insgesamt 48
drwxrwxr-x  5 sodaen sodaen    4096 Nov 13 18:06 .
drwxrwxr-x 44 sodaen sodaen   28672 Dez 17 17:02 ..
drwxrwxr-x  2 sodaen sodaen    4096 Nov 13 21:29 charts
drwxrwxr-x  2 sodaen www-data  4096 Nov 14 15:25 images
lrwxrwxrwx  1 root   root        58 Nov 11 11:41 stratgen-logo.svg -> /home/sodaen/stratgen/frontend/static/ui/stratgen-logo.svg
drwxrwxr-x  3 sodaen sodaen    4096 Nov 28 20:08 ui

templates/:
insgesamt 40
drwxrwxr-x  3 sodaen sodaen  4096 Okt  4 20:16 .
drwxrwxr-x 44 sodaen sodaen 28672 Dez 17 17:02 ..
```

## 5. HAUPTDATEIEN (Einstiegspunkte)
```
-rwxrwxr-x 1 sodaen sodaen  1360 Okt 17 11:44 changelog.py
-rw-rw-r-- 1 sodaen sodaen 14698 Dez 16 16:24 generate_deck_v2.py
-rw-rw-r-- 1 sodaen sodaen   517 Dez 16 12:43 gunicorn.conf.py
-rw-rw-r-- 1 sodaen sodaen 10186 Nov 30 00:37 patch_knowledge_enhanced.py
-rw-rw-r-- 1 sodaen sodaen  7959 Nov 30 00:37 patch_learning_adaptation.py
-rw-rw-r-- 1 sodaen sodaen  3876 Nov 29 19:50 patch_llm_call.py
-rw-rw-r-- 1 sodaen sodaen  6895 Nov 30 00:37 patch_multimodal_export.py
-rw-rw-r-- 1 sodaen sodaen  5087 Nov 30 00:37 patch_visual_intelligence.py
-rw-rw-r-- 1 sodaen sodaen 14947 Dez 16 16:24 slide_structure_engine.py
```

## 6. PPTX-GENERATOREN (Duplikate?)
```
services/asset_tagger.py
services/auto_learner.py
services/brand_voice_extractor.py
services/briefing_analyzer.py
services/content_intelligence.py
services/deck_filler.py
services/deck_templates.py
services/ds_ingest.py
services/export_api.py
services/export_ingest.py
services/export_service_v2.py
services/export_tools.py
services/feature_orchestrator.py
services/graph_extract.py
services/ingest.py
services/intelligent_deck_generator.py
services/knowledge_pipeline.py
services/knowledge.py
services/learn_engine.py
services/learning_adaptation.py
services/learn.py
services/learn_watcher.py
services/multimodal_export.py
services/ppt_renderer.py
services/pptx_designer.py
services/pptx_designer_v2.py
services/pptx_designer_v3.py
services/pptx_extract.py
services/pptx_ingest.py
services/self_learning.py
services/semantic_slide_matcher.py
services/slide_dna_analyzer.py
services/strategic_grammar.py
services/template_learner.py
services/templates.py
services/template_tools.py
services/unified_knowledge.py
services/vision_analyzer.py
```

## 7. LLM/CONTENT GENERATOREN
```
services/agent.py
services/argument_engine.py
services/briefing_analyzer.py
services/chart_generator.py
services/competitive_intelligence.py
services/content_generator_v2.py
services/critic.py
services/data_services.py
services/export_api.py
services/feature_orchestrator.py
services/generator.py
services/intelligent_deck_generator.py
services/knowledge_enhanced.py
services/knowledge_pipeline.py
services/knowledge.py
services/live_generator.py
services/llm_content.py
services/llm.py
services/multimodal_export.py
services/outline.py
```

## 8. API ENDPOINTS
```
@app.get("/api/generate/templates")
@app.get("/health")
@app.get("/ops/diag")
@app.post("/api/generate/intelligent")
@router.delete("/collections/{name}")
@router.delete("/delete")
@router.delete("/{file_path:path}")
@router.delete("/remove")
@router.delete("/{session_id}")
@router.delete("/tasks/{task_id}")
@router.get("")
@router.get("/active")
@router.get("/archetypes")
@router.get("/assets/preview/{project_id}")
@router.get("/benchmark")
@router.get("/chat/feedback/stats")
@router.get("/chunks/{collection}/{chunk_id}")
@router.get("/collections")
@router.get("/collections/{name}")
@router.get("/current")
@router.get("/daily", response_model=List[DailyUsage])
@router.get("/dashboard/all")
@router.get("/dashboard/ingestion")
@router.get("/dashboard/learning")
@router.get("/dashboard/optimization")
@router.get("/dashboard/overview")
@router.get("/dashboard/quality")
@router.get("/dashboard/search")
@router.get("/data/list", response_model=ListResp)
@router.get("/debug/info")
@router.get("/debug/ping", response_class=JSONResponse, tags=["observability"])
@router.get("/events", summary="Tail telemetry events (last N)", operation_id="telemetry_tail__telemetry_events")
@router.get("/export/{format}/{session_id}")
@router.get("/export/projects/{project_id}/export.md")
@router.get("/exports")
@router.get("/exports/download/{name}")
@router.get("/extracted")
@router.get("/features")
@router.get("/files/{folder}")
@router.get("/frameworks")
```

## 9. KONFIGURATION
```
REDACTED
REDACTED
REDACTED
REDACTED
REDACTED
REDACTED
REDACTED
REDACTED
REDACTED
REDACTED
REDACTED
REDACTED
REDACTED
REDACTED
REDACTED
REDACTED
REDACTED
export LLM_PROVIDER=ollama

# Unsplash API
```

## 10. GIT STATUS
```
 M CHANGELOG.md
?? SYSTEM_ANALYSIS.md
777bc980 auto: snapshot 2025-12-17T17:01:18+01:00
1f1ec3b7 auto: sync 2025-12-17 16:59:55
cf9a26fa auto: snapshot 2025-12-17T16:56:19+01:00
bdfe23b9 auto: sync 2025-12-17 16:54:53
783bc4f0 auto: snapshot 2025-12-17T16:50:18+01:00
662d86c7 auto: sync 2025-12-17 16:49:47
4ee6bc83 auto: sync 2025-12-17 16:44:47
36c8933a auto: snapshot 2025-12-17T16:44:18+01:00
ce664f99 auto: sync 2025-12-17 16:39:36
1d4cf358 auto: snapshot 2025-12-17T16:38:18+01:00
```

## 11. DATENBANK/STORAGE
```
insgesamt 83996
drwxrwxr-x  36 sodaen sodaen     4096 Dez 17 13:46 .
drwxrwxr-x  44 sodaen sodaen    28672 Dez 17 17:02 ..
drwxrwxr-x   2 sodaen sodaen     4096 Nov  3 11:32 agent-runs
-rw-rw-r--   1 sodaen sodaen     1073 Nov 26 19:31 agent_runs.jsonl
-rw-rw-r--   1 sodaen sodaen     1459 Nov 29 19:46 assets.json
-rw-r--r--   1 sodaen sodaen    81920 Dez  4 13:09 autolearn.sqlite
drwxrwxr-x   3 sodaen sodaen     4096 Okt  3 21:57 brands
-rw-r--r--   1 sodaen sodaen    32768 Nov 30 20:24 brand_voice.sqlite
drwxrwxr-x   2 sodaen sodaen     4096 Okt  3 00:24 cache
drwxrwxr-x   2 sodaen sodaen     4096 Dez 16 13:57 charts
drwxrwxr-x   2 sodaen sodaen     4096 Nov 10 16:11 config
drwxrwxr-x   2 sodaen sodaen     4096 Nov  2 19:50 content
-rw-r--r--   1 sodaen sodaen    24576 Nov  2 20:11 content.sqlite
drwxrwxr-x   2 sodaen sodaen     4096 Okt 13 20:14 corpus
drwxrwxr-x   2 sodaen sodaen     4096 Nov  3 10:07 critic
drwxrwxr-x   2 sodaen sodaen     4096 Nov  9 15:59 datasources
-rw-rw-r--   1 sodaen sodaen      354 Okt 20 13:27 eval_prompts.txt
drwxrwxr-x   5 sodaen sodaen    20480 Dez 17 17:02 exports
drwxrwxr-x   2 sodaen sodaen     4096 Dez  5 18:19 external
44K	data/agent-runs/
16K	data/brands/
248K	data/cache/
988K	data/charts/
4,0K	data/config/
48K	data/content/
934M	data/corpus/
16K	data/critic/
200M	data/datasources/
4,3M	data/exports/
4,0K	data/external/
4,0K	data/generated_outputs/
1,7M	data/images/
146M	data/knowledge/
204K	data/learn/
84K	data/live_sessions/
1,9M	data/metrics/
12K	data/missions/
16K	data/outlines/
1,7M	data/projects/
8,0K	data/providers/
2,3G	data/raw/
64K	data/raw-extracted/
8,0K	data/session_collections/
492K	data/sessions/
68K	data/snapshots/
4,0K	data/sources/
592K	data/strategies/
564K	data/style/
12K	data/styles/
16K	data/telemetry/
68K	data/templates/
12K	data/uploads/
```

## 12. ABHÄNGIGKEITEN
```
accelerate==1.10.1
aiofiles==24.1.0
aiohappyeyeballs==2.6.1
aiohttp==3.12.15
aiosignal==1.4.0
aiosqlite==0.21.0
annotated-types==0.7.0
antlr4-python3-runtime==4.9.3
anyio==4.11.0
attrs==25.3.0
backoff==2.2.1
banks==2.2.0
beautifulsoup4==4.14.2
cachetools==6.2.0
cbor==1.0.0
certifi==2025.8.3
cffi==2.0.0
charset-normalizer==3.4.3
click==8.3.0
colorama==0.4.6
coloredlogs==15.0.1
contourpy==1.3.3
cryptography==46.0.2
cycler==0.12.1
dataclasses-json==0.6.7
datasets==4.1.1
defusedxml==0.7.1
Deprecated==1.2.18
dill==0.4.0
dirtyjson==1.0.8
diskcache==5.6.3
distro==1.9.0
effdet==0.4.1
emoji==2.15.0
fastapi==0.118.0
filelock==3.19.1
filetype==1.2.0
FlagEmbedding==1.2.10
flatbuffers==25.9.23
fonttools==4.60.1
frozenlist==1.7.0
fsspec==2025.9.0
google-api-core==2.25.1
google-auth==2.41.1
google-cloud-vision==3.10.2
googleapis-common-protos==1.70.0
greenlet==3.2.4
griffe==1.14.0
grpcio==1.75.1
grpcio-status==1.75.1
```
