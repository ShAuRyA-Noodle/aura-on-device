---
slide: 6
title: Open Datasets planned to be used / published
---
## BODY
Six datasets in. Three datasets out.
LSApp, Tsinghua, Melbourne for training. Pew, WHO, Kantar for framing.
Pilot CSV publishes with submission.

## SPEAKER NOTES
Six datasets we use. LSApp from arxiv 1911.04026 trains the next-app LSTM, public, research license. Tsinghua App Usage Trace augments it with geographic and temporal features. Melbourne Context Query Logs we use as adversarial input, heterogeneous queries that stress-test the orchestrator's decision routing. Pew Research, WHO adolescent mental health, and Kantar Gen Z India are framing citations only, no model touches them. Health Connect synthetic and real HRV samples come from per-user opt-in collection. Crucially, three datasets we will publish: anonymised pilot telemetry from thirty users, the Indian SMS and Gmail receipt parser corpus assembled with consent, and the Load Score versus self-rated stress correlation table. That is the verifiable raw evidence the brief asks for. Every figure in this deck has a citation tag. Every number we cannot yet measure carries a [TEAM TO VERIFY] tag instead of a guess.

## CITATIONS
[15] LSApp, https://arxiv.org/abs/1911.04026.
[16] Pew teens and technology, https://www.pewresearch.org/topic/internet-technology/teens-internet-technology/.
[17] WHO adolescent mental health, https://www.who.int/news-room/fact-sheets/detail/adolescent-mental-health.
[18] Kantar Gen Z, https://www.kantar.com/inspiration/research-services/genz.
[3] Health Connect. [9] HealthKit.
Tsinghua App Usage Trace and Melbourne Context Query Logs [TEAM TO VERIFY exact source URLs; add to plan.md §37.1 before submission].

## VISUAL BRIEF
Two-column index card. Cols 1-7 list six datasets, each as a 96 px row: dataset name in Fraunces 32 pt, role in Inter Tight 18 pt at 60% opacity, license in JetBrains Mono 14 pt right-aligned, 1 px hairline at 20% between rows. Rows: LSApp / Tsinghua App Usage Trace / Melbourne Context Query Logs / Pew, WHO, Kantar (framing) / Health Connect samples / Custom 30-user pilot telemetry. Cols 8-12 hold a single highlighted block with sunset-orange #FF5B2E top edge 4 px: heading Data we will publish in Fraunces 32 pt, then three lines: 30-user pilot telemetry (anonymised CSV), Indian SMS and Gmail receipt parser corpus, Load Score to self-rated stress correlation table. Bottom strip 14 pt sans: Every figure has a citation tag. Raw data publishes with submission. Reference: Hugging Face dataset cards, arxiv abstract pages.

## PERSUASION JOB
Show verifiable raw evidence and lift the team out of the demo-only category for the Engineer and Business judges.
