# Local LLM for dewmark: serving, browser access, models, evidence, regulation, and an API contract

*Research as of 2026-09-27. Both repos were only read. Scratch downloads are in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/llm-research/`.*

## Bottom line

1. **Build to one API: OpenAI Chat Completions.** That means `POST /v1/chat/completions`, `response_format: {type:"json_schema"}` and `GET /v1/models`. Ollama, llama.cpp, vLLM, LM Studio, LocalAI and Jan all serve it. The Responses API is now widely served too, but Ollama only supports it without server-side state. Keep it as an option for later, not the base.
2. **The awkward parts are in the browser, not the model.** A page opened by double-click (file://) sends `Origin: null`. Ollama's built-in allowlist does not match that, so it answers 403 unless the teacher sets `OLLAMA_ORIGINS=*`. Chrome 142+ also asks the user before a public https page may reach a LAN or localhost address. The Python builder avoids all of this.
3. **"Runs locally, teacher decides" solves most of the GDPR problem. It does not solve the AI Act problem.** The Commission's May 2026 draft guidelines name "AI-enabled grading and feedback systems … proposing grades" for tests that count as **high-risk**. They also say a system that produces "a specific recommendation or evaluation of the case" cannot count as merely preparatory. For stand-alone Annex III systems the high-risk rules now apply from **2 December 2027** (Digital Omnibus, Reg. (EU) 2026/1744).
4. **The research supports "suggestion + evidence, teacher confirms" but warns it is not enough on its own.** Agreement with human markers is moderate. Local 20–30B models are more open to "give me full marks" injections than frontier models. A 2026 PNAS Nexus experiment with more than 1,300 teachers found they were *less* likely to correct harsh AI grades than the same grades from a human.
5. **The most useful features are also the safest.** Converting an exam, checking a paper's quality, drafting a marking scheme, and checking the teacher's own marks for consistency afterwards are all outside Annex III or covered by exceptions the Commission names. Suggesting marks on summative papers should be left out.

---

## 1. Serving options and their HTTP APIs

| Server | Default bind | OpenAI Chat Completions | Responses API | Structured output | Model list / capabilities | CORS default | Auth |
|---|---|---|---|---|---|---|---|
| **Ollama** | `127.0.0.1:11434` | yes (`/v1`) | yes, **stateless only** ("no `previous_response_id` or `conversation`") | native `/api/chat` `format: <JSON Schema>`; `/v1` maps `response_format.json_schema.schema` to the same (source: `openai/openai.go` L758-763; `strict` and `name` are ignored) | `/v1/models`, `/api/tags`, `POST /api/show` → `capabilities[]` (completion, vision, thinking, tools…), `remote_host` | fixed list (below) + `OLLAMA_ORIGINS` | none |
| **llama.cpp `llama-server`** | `127.0.0.1:8080` | yes | yes (converted internally to chat) | `response_format` `json_object` / `json_schema`, plus GBNF grammars | `/v1/models`, `/props`, `/health`; router mode (`--models-dir`) | **reflects any Origin, credentials allowed** (`--cors-origins` to restrict) | `--api-key` |
| **vLLM** | `:8000` | yes | yes | `response_format` json_schema; `structured_outputs: {json, regex, choice, grammar}` (old `guided_*` fields deprecated) | `/v1/models`, `/health` | `--allowed-origins` (default `*`) | `--api-key` |
| **LM Studio** | `localhost:1234` | yes | yes (since 0.3.29) | json_schema via llama.cpp grammars (GGUF) / Outlines (MLX); docs: "Not all models are capable … particularly LLMs below 7B" | `/v1/models` | toggle / `lms server start --cors` | off by default; cannot be enabled from the CLI (lms issue #489) |
| **LocalAI** | `:8080` | yes | yes ("Open Responses") | `grammar` (BNF), `grammar_json_functions`; llama.cpp backend only | `/v1/models` | configurable | optional key |
| **Jan** | `127.0.0.1:1337` | yes (`/v1`) | not documented | not documented | `/v1/models` | "Enabled by default" | optional key, trusted hosts |

**Streaming.** Every server streams Chat Completions as Server-Sent Events (`data: {...}` … `data: [DONE]`). Ollama's native `/api/*` streams newline-delimited JSON instead, and streams by default (`stream` defaults to true).

**The newer standard.** "Open Responses" (openresponses.org, 2026) is an open spec based on OpenAI's Responses API. Ollama, vLLM and LM Studio say they support it. It adds agent and tool orchestration, which dewmark does not need.

**Ollama details that matter for dewmark:**
- **Cloud models.** Tags ending `-cloud` (for example `gemma4:31b-cloud`, `gpt-oss:20b-cloud` on ollama.com/library) are answered by Ollama's own servers through the same localhost API. `/api/show` and `/api/tags` expose `remote_host` / `remote_model` for these (`api/types.go` L668, L750). `OLLAMA_NO_CLOUD=1` turns cloud inference off (`envconfig/config.go` L237, L332). dewmark should refuse any model that reports a `remote_host`.
- **Context length.** The FAQ says the default is 4096 tokens. Current source says "4k/32k/256k based on VRAM" (`OLLAMA_CONTEXT_LENGTH`, config.go L230, L338). An exam, its scheme and one answer can overflow 4k and be cut off without warning. The `/v1` layer has no per-request `num_ctx`, so either the setup guide sets `OLLAMA_CONTEXT_LENGTH=16384`, or dewmark uses native `/api/chat` with `options.num_ctx` when it detects Ollama.
- **Concurrency.** `OLLAMA_NUM_PARALLEL` defaults to 1, so a batch job should send one request at a time.
- **Other APIs.** Ollama now also serves `/v1/messages` (Anthropic-style) and `/v1/responses` (routes.go L1974-1985).

## 2. Calling the model from a web page

**CORS**
- **Ollama's default allowlist** (config.go L86-108) is `http(s)://localhost|127.0.0.1|0.0.0.0` on any port, plus `app://*`, `file://*`, `tauri://*` and `vscode-*`. `OLLAMA_ORIGINS` *adds* to that list.
- **file:// pages.** A file:// page sends `Origin: null`. `gin-contrib/cors` compares origins by prefix, so `null` does not match `file://*` and Ollama replies 403. The fix is `OLLAMA_ORIGINS=*`, or serving the workbench from `http://localhost:<port>`, which the default list already allows. *This comes from reading the source, not from running it; test it on a real install.*
- **Other servers.** llama.cpp and vLLM accept every origin by default. That is permissive: any website the teacher has open could call a LAN model unless something else blocks it. Recommend `--cors-origins` and `--api-key` on a shared box.

**Chrome Local Network Access (LNA)**
- **When it prompts.** Since Chrome 142, a request from a *public* origin to a *local* (RFC1918, `.local`) or *loopback* address needs the user's permission. The permission can only be requested from a secure context.
- **Split permission.** Chrome 145/146 split it into `local-network` and `loopback-network`, and Permissions-Policy uses the same names. Chrome 147 extends the check to WebSockets and WebTransport.
- **Mixed content.** An https page may make an http request to a private address only if the host is a private IP literal, a `.local` name, or the fetch sets `targetAddressSpace: "local" | "loopback"`.
- **Requests that do not prompt.** local→local and loopback→anything are not treated as local-network requests.
- **file:// pages.** The spec says: "let's err on the side of treating file URLs as local" (WICG LNA §4.1). So a file:// workbench calling localhost or the LAN box should not prompt. Verify this on the ETB's Chrome build.
- **Enterprise policies.** They exist now; finer-grained ones are "to be added later".
- **Firefox** now shows its own local-network prompt, with some regressions (Bugzilla 2059274). Safari has shown no interest in the spec.

**Recommended layouts, best first**
1. **Python builder calls the model** (`build_exam.py` via `urllib`). No CORS, no LNA, no browser. This suits conversion and paper checking.
2. **Workbench opened as file:// → `http://localhost:11434` or `http://<box-ip>:11434`.** File System Access keeps working, since the workbench already relies on file:// for that (`docs/FOR_TEACHERS.md` L83-97). It needs `OLLAMA_ORIGINS=*`, or `--cors-origins` for llama.cpp.
3. **Box serves the workbench and proxies `/v1` from the same origin.** No CORS and no LNA. But `http://192.168.x.x` is **not a secure context**, so `showDirectoryPicker` fails. That needs TLS on the box or the Chrome policy `OverrideSecurityRestrictionsOnInsecureOrigin`, which is extra IT work.
4. **Hosted https page → LAN box.** This triggers the LNA prompt and hits mixed-content and Safari gaps. Avoid it.
5. **Student pages.** They should never contain LLM client code. Add `connect-src` restrictions so the student page cannot reach the teacher's box.

## 3. Models that fit modest hardware

All of these are open-weight. Parameter counts come from the HF API; memory figures are approximate for Q4 quantisation.

| Family (licence) | Sizes | Fits | Notes |
|---|---|---|---|
| **Qwen3.8-27B** (Apache-2.0, Aug 2026) | 27B dense, understands images, 262k context | 24 GB GPU at Q4 (~17 GB); 16 GB GPU only at ~IQ3 with ~8k context; Mac with ≥32 GB | Best all-rounder in this class for code, reasoning and reading documents. Thinking can be switched off per request. `ollama: qwen3.8:27b` |
| **Qwen3.6-35B-A3B** / **Qwen3.5-9B/4B** (Apache-2.0) | MoE with 3B active; dense 9B/4B | the MoE is fast on CPU or a Mac with ≥32 GB RAM; 9B/4B on 8–16 GB | The CPU-only choice |
| **Gemma 4** (Apache-2.0, Mar–Jul 2026) | E2B, E4B, 12B, 26B-A4B (MoE), 31B | 31B → 24 GB GPU; 26B-A4B → 16–24 GB or a Mac; E4B/12B → 8–16 GB | Good prose for feedback and schemes |
| **gpt-oss-20b** (Apache-2.0, Aug 2025) | 21B MoE, 3.6B active | ~16 GB; fine on a 16 GB Mac mini or CPU | Strong reasoning for its size; text only |
| **Ministral 3** (Apache-2.0) | 3B / 8B / 14B, plus reasoning variants | 8–16 GB | EU vendor, if that matters to procurement |
| **Document/OCR models** | GLM-OCR 1.3B (MIT), DeepSeek-OCR-2 3.4B, chandra-ocr-2 5.3B, olmOCR-2 7B, granite-docling 258M | CPU or small GPU | For scanned PDFs and handwritten maths: output is Markdown/LaTeX to feed the main model |

**Which model for which task**
- **Word/PDF → exam file.** Don't have a model *read* .docx files. Convert them deterministically first (mammoth.js in the browser, or pandoc/Docling in the builder). Use OCR models only for scans. Then have Qwen3.8-27B or Gemma 4 31B restructure the text into the dewmark format under a schema. The builder's strict checks stay as the backstop (`planning/TRANSLATING_AN_EXISTING_EXAM.md` §1).
- **Model answers and schemes.** Use the largest local model with thinking on.
- **Short-answer rubric checks and Python review.** Qwen3.8-27B, gpt-oss-20b or Qwen3.6-35B-A3B. For code, always pair the model with actually running the code in Pyodide; the model explains test results rather than guessing behaviour.
- **Small models.** Avoid anything under ~8B for judgement tasks. An 18-model study found "mini" and "nano" variants consistently underperformed.

## 4. Evidence on LLM-assisted marking

**Agreement with human markers is moderate**
- Short answers in sustainability education: LLM-to-human QWK 0.585–0.640, against human-to-human ICC 0.667–0.800. Agreement falls as the cognitive demand rises (Emirtekin, *JCAL* 2026).
- 18 LLMs on more than 6,000 intro-programming submissions: "high internal agreement" between models but "only moderate agreement with human teachers' grades" (arXiv 2509.26483).
- Mathematics exam grading with 2026 frontier models: best total-score Pearson r = 0.58 (arXiv 2607.01247).
- Estonian national school-leaving essays: scores fell "within the human scoring range", but only inside a "rubric-driven, human-in-the-loop" pipeline (arXiv 2601.16314).
- Calibrated selective grading: the model scores 35–65% of answers itself and passes the rest to humans. The answers it keeps reach QWK ≥ 0.80 (CHiL(L)Grader, arXiv 2603.11957). The design lesson is to show confidence and send uncertain answers to the teacher.
- Most of these studies used frontier cloud models. Expect local 20–30B models to do worse.

**Bias**
- With explicit "judge content only" instructions, Llama-3.3-70B and Qwen-2.5-72B still took off 1.90 and 1.20 points out of 10 for informal language, and 1.35 and 0.90 for non-native phrasing (arXiv 2603.18765). That matters for Dublin FET classes with many learners whose first language is not English.
- Leniency also varies by the writer's first language (TOEFL studies).

**Prompt injection**
- Wharton GAIL (April 2026): frontier models moved +2.6 percentage points on average under injected instructions; GPT-4o-mini moved about +20 pp. Models flagged the injection in only 1.4% of trials.
- Li et al. 2026 (arXiv 2606.03090): LLM grading systems "remain highly vulnerable".
- Assume local models behave like the small-model case.

**Automation bias**
- Goulas et al., *PNAS Nexus* 2026, with more than 1,300 teachers: "the grading fairness gap was 22% larger for harsh AI errors". The effect was strongest among tech-confident teachers.
- A "confirm" button is therefore not an adequate safeguard. Blind-first marking is: the teacher enters a mark, then sees the model's view.

**What the evidence supports**
- The model produces **per-criterion observations with a verbatim evidence quote**. It never produces a final mark.
- dewmark checks that each quote is an exact substring of the answer and drops any that are not.
- Student text goes only in the user turn, wrapped in random-nonce delimiters.
- The schema clamps marks to `[0, max]`.
- A plain regex also flags zero-width or hidden characters and phrases aimed at an AI.
- The Irish Department of Education's AI guidance (Oct 2025, p.15) says: "teachers and schools leaders must act as the final checkpoint, systematically reviewing and validating all AI-generated outputs".

## 5. Regulation

**Annex III point 3(b)** covers "AI systems intended to be used to evaluate learning outcomes, including when those outcomes are used to steer the learning process of natural persons in educational and vocational training institutions at all levels." Point 3(d), monitoring prohibited behaviour during tests, also matters if dewmark ever flags "suspicious" answers.

**Timeline**
- Prohibitions and Article 4 (AI literacy): 2 Feb 2025.
- General-purpose AI obligations: 2 Aug 2025.
- **Digital Omnibus, Reg. (EU) 2026/1744:** published in the Official Journal 24 July 2026, in force 27 July 2026. Stand-alone Annex III obligations move from 2 Aug 2026 to **2 Dec 2027**; Annex I products to 2 Aug 2028.
- Article 50 transparency rules keep the Aug 2026 date, with a short grace period for machine-readable marking.
- Article 4 is softened to deployers "support the development of AI literacy".
- The Irish DoE guidance says "apply in full from 2 August 2027". That predates the Omnibus and is out of date.

**How classification works (draft Commission guidelines, May 2026)**

These are drafts: consultation closed 23 June and the final version is expected by the end of 2026.
- Para 223: only **summative** evaluation is in scope, including "intermediate grades that are considered in the final evaluation". QQI exams qualify.
- **In scope:** "AI-enabled grading and feedback systems … which count towards a final evaluation … proposing grades."
- **Exempt under 6(3)(b):** an "exam quality checker … for errors, such as grammatical issues, ambiguous wording, or inconsistencies with the rubric … teacher remains responsible".
- **Exempt under 6(3)(c):** an "assessment review tool" that flags deviations in an instructor's grading patterns for human review. This matches Recital 53: "check ex post whether the teacher may have deviated from the grading pattern".
- **Para 108:** "Where the AI system is intended to produce a specific recommendation or evaluation of the case … [it] can therefore not be considered to perform a preparatory task." So human confirmation does not remove mark suggestion from high-risk.
- **Para 224:** formative feedback in ongoing learning is not high-risk, *unless the teacher uses it for grades*.
- **Rule-based checks are not AI.** Recital 12 excludes rules "defined solely by natural persons", so comparing answers to an MCQ key or running unit tests falls outside the AI Act.

**Deployer duties (a teacher or ETB using a high-risk system)**
- Art. 26: use it according to the instructions; give human oversight to people with "the necessary competence, training and authority" (26(2)); make sure input data is relevant (26(4)); monitor use; keep logs for at least 6 months (26(6)); tell the people affected (26(11)); public authorities must register (26(8)); use the provider's information for a DPIA (26(9)).
- **Art. 27 fundamental-rights impact assessment:** required for "bodies governed by public law", which covers ETBs.

**The provider question (needs legal confirmation)**
- The open-source exemption (Art. 2(12)) does not apply to systems "put into service as high-risk".
- Under Art. 25, anyone who gives a general-purpose model a high-risk intended purpose becomes its provider. That brings conformity assessment, technical documentation and registration.
- If dewmark ships "suggest marks for exams", Josh or the ETB would carry those duties from Dec 2027.

**GDPR and the Irish DPC**
- Exam answers and examiner comments are personal data (CJEU C-434/16 *Nowak*, a reference from Ireland). Stored model suggestions and rationales fall inside a subject access request.
- The DPC's 2024 LLM guidance: "If outputs … are relied upon without critical human analysis … you may be introducing automated decision making risks." CJEU *SCHUFA* (C-634/21) shows that a machine score which plays a determining role can bring Art. 22 into play, which is the rubber-stamping risk.
- The DoE guidance says to avoid entering personal data where the tool's terms are unclear.

**What "local + teacher decides" changes**
- **GDPR: a lot.** There is no processor, no third-country transfer, and dewmark can strip names and numbers before a prompt is built. The ETB is still the controller, and a DPIA is prudent.
- **AI Act: little.** Classification follows intended purpose, not where the model runs or who presses confirm. Teacher oversight is *required*, but it does not take a feature out of scope. **Choosing which features to build does.**

## 6. In-browser options with no server

| Option | Status (Sep 2026) | Limits |
|---|---|---|
| **WebLLM** 0.2.85 (8 Sep 2026) | Chat API in the OpenAI shape; JSON-schema output; Web Worker support; weights can be self-hosted | Needs WebGPU. Largest practical model is Qwen3-8B q4f16 at `vram_required_MB: 5695`, with a **4096-token** context. Too weak and too small for marking; possible for paper checks on good hardware |
| **transformers.js** 4.3.0 (16 Sep 2026) | Rewritten WebGPU runtime; supports >8B models, gpt-oss | Best use is **embeddings**: grouping similar answers for batch marking, which works on ordinary school PCs. Also small OCR/classification models |
| **Chrome Prompt API** (Gemini Nano) | Available to web pages from Chrome 148 (May 2026), over objections from Mozilla, WebKit and the W3C TAG; Edge turned it off | 22 GB free disk; >4 GB VRAM, or 16 GB RAM and 4 cores; languages en/ja/es/de/fr only; small context; `responseConstraint` accepts a JSON schema. Chrome-only, so use it as an optional extra at most |

## 7. Proposed minimal API contract

**Settings**, stored per teacher in localStorage and never in the exam file:

```
{ baseUrl: "http://localhost:11434/v1", apiKey?: "", model: "qwen3.8:27b" }
```

**1. Discovery**, run by a **Test connection** button:
- `GET {baseUrl}/models` returns `{data:[{id}]}`. This works on all six servers.
- Optional probes; any failure is ignored:
  - `GET {origin}/api/version` identifies Ollama. Then `POST /api/show {model}` gives `capabilities`, `remote_host`, context length and digest.
  - `GET {origin}/props` identifies llama.cpp and gives `n_ctx`.
- The result is a capability record:

```
{server, model, digest?, ctx, vision, structured:"json_schema"|"json_object"|"none", remote:false}
```

- Refuse to continue if `remote_host` is set. Show "Local only ✓".
- Diagnose failures in plain language:
  - 403 or opaque CORS error → "set OLLAMA_ORIGINS"
  - network TypeError → "server not running, or the browser blocked local access"
  - 401 → "API key"
  - context under 8k → warning

**2. Call**, one request at a time, cancellable with AbortController, with a timeout:

```
POST {baseUrl}/chat/completions
{ model, temperature: 0, seed: 1, max_tokens: 2000, stream: true,
  messages: [
    {role:"system", content: TASK["check_paper.v1"].instructions},
    {role:"user", content: "<exam nonce=K3f9>…</exam>\n<scheme nonce=K3f9>…</scheme>"}],
  response_format: {type:"json_schema",
    json_schema:{name:"dewmark_check_paper_v1", strict:true, schema:{…}}} }
```

Streaming is used only to show progress. Parse the result once it is complete.

**3. Versioned task schemas** kept in the repo. Use only enums, integers with min/max, `required`, and no `oneOf`, because grammar backends support only part of JSON Schema. For example:

```json
{"issues":[{"question":"q3b","kind":"ambiguous|marks_dont_add_up|key_disagrees|reading_level|other",
  "quote":"…exact text…","explanation":"…","suggestion":"…"}]}
```

**4. Validate, then fall back step by step:**
1. Validate against the schema, with an exact-substring check on every `quote`.
2. If that fails, retry once and include the validation errors.
3. If the server does not support `json_schema`, retry with `json_object`, the schema in the prompt, and the same validator.
4. If there is still no usable server, switch to **Copy task / paste result**. dewmark produces the prompt and schema, the teacher runs them in any tool their ETB has approved, and pastes the JSON back through the same validator.
5. With no endpoint configured at all, the assistant UI is **absent** apart from one settings line. Every core feature works without it.

**5. Record keeping.** Each suggestion is written to the marking record with `{task version, model, digest, server, params, input hash, output, teacher decision, changed?}`. This covers the 6-month log duty and subject-access requests. The input hash also acts as a cache key so the same work is not run twice.

**Teacher-facing tasks, ranked by value against risk**

| # | Task | Value | AI Act position | Risk |
|---|---|---|---|---|
| 1 | Convert a Word/PDF exam and scheme into an exam file (builder, validation loop) | very high | not evaluating learners; "transforms unstructured data into structured data" (Recital 53) | low |
| 2 | Paper quality check: ambiguity, marks adding up, key disagreeing with scheme, reading level | high | named 6(3)(b) exemption | low |
| 3 | Draft model answers and marking schemes, labelled `draft` (existing rule) | high | outside Annex III | medium (a wrong key misdirects marking; the label handles this) |
| 4 | Suggest question types from a module descriptor (Q19) | medium | outside | low |
| 5 | Group similar answers so the teacher marks them together (embeddings, can run in-browser) | high | preparatory: "indexing … linking" | low (must not rank answers) |
| 6 | After marking, check the teacher's own marks for consistency ("these two near-identical answers got 3 and 1") | high, and helps moderation | named 6(3)(c) exemption / Recital 53 | low |
| 7 | Turn the teacher's own notes into feedback wording once the mark is decided | medium | 6(3)(b), "improve the language" | low |
| 8 | Feedback on *practice* papers, never used for grades | medium | formative, para 224 | medium |
| 9 | Python code review against a task, alongside Pyodide test runs | high | high-risk if summative | high |
| 10 | Mark suggestions with evidence on summative papers | highest time saving | **high-risk from 2 Dec 2027** | high: bias, injection, anchoring |

---

## What this means for dewmark

- **Adopt the contract in §7 as an optional "assistant" layer.**
  - Base it on Chat Completions with `json_schema` and `/v1/models`.
  - Add Ollama-specific extras only for the safety checks (`remote_host`) and context length.
  - Keep the Responses API off the critical path.
- **Put model calls in teacher tools only.**
  - The Python builder handles conversion and paper checks, with no browser problems.
  - The workbench, opened as file://, handles consistency checks and feedback wording.
  - Student pages get no LLM code and a restrictive `connect-src`.
- **Write a one-page setup recipe for teachers:**
  - Ollama with `OLLAMA_ORIGINS=*`, `OLLAMA_NO_CLOUD=1`, `OLLAMA_CONTEXT_LENGTH=16384`, `qwen3.8:27b` (24 GB GPU) or `gpt-oss:20b` / `gemma4:26b` (16 GB GPU or Mac mini).
  - llama-server with `--cors-origins` and `--api-key` for a shared box.
  - Rehearse it on the room's own machines, as `FOR_TEACHERS.md` already advises for Pyodide.
- **Scope decision: ship tasks 1–7 and do not ship 9–10 for summative exams.**
  - This keeps dewmark, Josh and the ETB clear of high-risk provider and deployer duties, including the Art. 27 fundamental-rights assessment.
  - If 9–10 are ever trialled: practice papers only, off by default, and the teacher marks before the model's view is shown. The anchoring evidence and the 6(3)(c) exemption both point to marking first.
- **Planning-doc updates:**
  - `planning/TRANSLATING_AN_EXISTING_EXAM.md`: name this API as "the assistant".
  - `planning/OPEN_QUESTIONS.md` Q15 and Q19: add the AI Act classification. Deterministic MCQ and test-case checks are not "AI" under Recital 12, which makes Q15's pre-checking a lower-stakes decision than the doc assumes.
  - `planning/THE_MARKING_WORKBENCH.md` §7: record the blind-first and record-keeping rules.
- **Branding and settings-screen link.** An "Assistant: connected / local only / not configured" status belongs on the *teacher's* settings screen. The student settings and loading screen should not depend on a model at all.
- **Get legal input.** Have the ETB's DPO or legal adviser confirm the provider reading (Art. 2(12) and Art. 25) before 2 Dec 2027. The draft guidelines may change when finalised at the end of 2026.

### Sources
- [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility) · [Ollama FAQ](https://docs.ollama.com/faq) · [Ollama /api/chat](https://docs.ollama.com/api/chat) · [ollama envconfig/config.go](https://github.com/ollama/ollama/blob/main/envconfig/config.go) · [Ollama structured outputs](https://ollama.com/blog/structured-outputs)
- [llama.cpp server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) · [vLLM online serving](https://docs.vllm.ai/en/latest/serving/online_serving/) · [vLLM structured outputs](https://docs.vllm.ai/en/latest/features/structured_outputs/)
- [LM Studio OpenAI compatibility](https://lmstudio.ai/docs/developer/openai-compat) · [LM Studio structured output](https://lmstudio.ai/docs/developer/openai-compat/structured-output) · [LM Studio 0.3.29 Responses](https://lmstudio.ai/blog/lmstudio-v0.3.29) · [lms issue #489](https://github.com/lmstudio-ai/lms/issues/489)
- [LocalAI constrained grammars](https://localai.io/features/constrained_grammars/) · [Jan API server](https://www.jan.ai/docs/desktop/api-server) · [Open Responses](https://www.openresponses.org/)
- [Chrome LNA blog](https://developer.chrome.com/blog/local-network-access) · [WICG LNA spec](https://wicg.github.io/local-network-access/) · [LNA explainer](https://github.com/WICG/local-network-access/blob/main/explainer.md) · [chromestatus LNA split](https://chromestatus.com/feature/5068298146414592) · [MDN Local network access](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Local_network_access) · [Bugzilla 2059274](https://bugzilla.mozilla.org/show_bug.cgi?id=2059274)
- [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) · [Gemma 4 31B](https://huggingface.co/google/gemma-4-31B-it) · [gpt-oss-20b](https://huggingface.co/openai/gpt-oss-20b) · [GLM-OCR](https://huggingface.co/zai-org/GLM-OCR) · [BenchLM local LLMs Sep 2026](https://benchlm.ai/best/local-llm)
- [Emirtekin 2026 JCAL](https://onlinelibrary.wiley.com/doi/10.1002/jcal.70160) · [arXiv 2509.26483](https://arxiv.org/abs/2509.26483) · [arXiv 2607.01247](https://arxiv.org/abs/2607.01247) · [arXiv 2601.16314](https://arxiv.org/abs/2601.16314) · [arXiv 2603.11957](https://arxiv.org/abs/2603.11957) · [arXiv 2603.18765](https://arxiv.org/html/2603.18765)
- [Wharton GAIL prompt injection](https://gail.wharton.upenn.edu/research-and-insights/hidden-prompt-injections/) · [arXiv 2606.03090](https://arxiv.org/html/2606.03090) · [PsyPost on Goulas et al. PNAS Nexus](https://www.psypost.org/teachers-say-they-distrust-ai-but-still-accept-its-harsh-grading-mistakes-study-finds/)
- [AI Act Annex III](https://artificialintelligenceact.eu/annex/3/) · [Art. 6](https://artificialintelligenceact.eu/article/6/) · [Art. 26](https://artificialintelligenceact.eu/article/26/) · [Art. 27](https://artificialintelligenceact.eu/article/27/) · [Art. 2](https://artificialintelligenceact.eu/article/2/) · [Recital 53](https://artificialintelligenceact.eu/recital/53/)
- [Draft high-risk guidelines PDF](https://table.media/assets/documents/draft_guidelines_on_the_classification_of_high_risk_ai_annex_iii_7mxr3yiz2gw3uppjpwvvndd8ioi_128561.pdf) · [Freshfields on the draft](https://www.freshfields.com/en/our-thinking/blogs/technology-quotient/eu-ai-act-unpacked-32-draft-commission-guidelines-on-high-risk-ai-implicati-102n1bn)
- [K&L Gates / Cyber Law Watch on the Omnibus](https://www.cyberlawwatch.com/2026/07/31/eu-digital-omnibus-on-ai-enters-into-force/) · [Gibson Dunn](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/)
- [Irish DoE AI guidance Oct 2025](https://assets.gov.ie/static/documents/dee23cad/Guidance_on_Artificial_Intelligence_in_Schools_2025.pdf) · [DPC AI/LLMs blog](https://www.dataprotection.ie/en/dpc-guidance/blogs/AI-LLMs-and-Data-Protection)
- [WebLLM](https://github.com/mlc-ai/web-llm) · [Transformers.js v4](https://huggingface.co/blog/transformersjs-v4) · [Chrome Prompt API](https://developer.chrome.com/docs/ai/prompt-api) · [TechTimes on Prompt API shipping](https://www.techtimes.com/articles/316729/20260516/google-ships-chrome-prompt-api-over-objections-mozilla-apple-w3c-microsoft.htm)