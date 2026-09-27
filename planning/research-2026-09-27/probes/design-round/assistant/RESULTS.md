# Assistant probes, 2026-09-27 (scratch)
Ollama 0.34.4 (linux-amd64 release, CPU libs only), model qwen3:0.6b (Q4_K_M) from registry.ollama.ai.
llama-server bundled in the same release (lib/ollama/llama-server, build b1-161755f29), same GGUF.
Chromium 141.0.7390.37 headless (Playwright), pages opened from file://.

1. Ollama default origins: Origin null -> 403 (GET and preflight); file:// -> 200; http://localhost:8000 -> 200; https://deweydex.github.io -> 403.
2. OLLAMA_ORIGINS=null or "https://deweydex.github.io,null" -> server does not start: "panic: bad origin: origins must contain '*' or include http://,https://,chrome-extension://,..."
3. OLLAMA_ORIGINS=https://deweydex.github.io -> that origin 200, null 403, others 403.  OLLAMA_ORIGINS=* -> everything 200.
4. Browser, file:// page, default origins: cors fetch -> "TypeError: Failed to fetch"; no-cors fetch to running server -> opaque response (resolves); no-cors fetch to closed port -> TypeError. So a no-cors probe separates "blocked by origin rules" from "nothing listening".
5. CSP meta injected by the first script in <head> (connect-src http://127.0.0.1:11434) is enforced in a file:// page: other ports refused, securitypolicyviolation fired; it also blocked Playwright's eval (so tests must read the DOM).
6. Streaming + AbortController: AbortError in page; server log "srv stop: cancel task" (generation stops). AbortSignal.timeout(300) -> TimeoutError.
7. Wrong model on Ollama /v1 -> 404 {"error":{"message":"model 'qwen3.8:27b' not found","type":"not_found_error",...}}
8. Context: Ollama with no GPU chose default_num_ctx=4096 ("vram-based default context"). /api/ps shows "context_length":4096 for the loaded model; /api/show gives the trained maximum (qwen3.context_length 40960).
9. Ollama /v1/chat/completions with a 7,189-token prompt: HTTP 200, log "truncating input prompt limit=2050 prompt=7189 keep=4 new=2050", usage.prompt_tokens=2050; the reply was about "Question 188" (it saw only the end).
10. Ollama native /api/chat with "truncate":false,"shift":false, num_ctx 4096 -> HTTP 400 {"error":"{\"error\":{\"code\":400,\"message\":\"request (7189 tokens) exceeds the available context size (4096 tokens), try increasing it\",\"type\":\"exceed_context_size_error\",\"n_prompt_tokens\":7189,\"n_ctx\":4096}}"}. With num_ctx 16384 -> 200, prompt_eval_count 7189 (46 s of prompt reading on 4 CPU cores).
11. llama-server /v1 with the same prompt at -c 4096 -> HTTP 400 {"error":{"code":400,"message":"request (7185 tokens) exceeds the available context size (4096 tokens), try increasing it","type":"exceed_context_size_error","n_prompt_tokens":7185,"n_ctx":4096}}
12. GET /api/status (Ollama) -> {"cloud":{"disabled":true,"source":"env"}} with OLLAMA_NO_CLOUD=1; {"cloud":{"disabled":false,"source":"none"}} without.
13. llama-server --api-key: no or wrong key -> 401 {"error":{"message":"Invalid API Key","type":"authentication_error","code":401}}, readable from a file:// page (CORS headers present). /health needs no key. /props -> default_generation_settings.n_ctx 4096, modalities {vision:false,...}.
14. llama-server --cors-origins "null,https://deweydex.github.io" echoed the whole list as Access-Control-Allow-Origin (browsers reject that). A single value (null) works from file://.
15. JSON Schema features (Ollama format / llama-server json_schema): enum, maxItems, minimum/maximum, required, additionalProperties:false enforced by both; maxLength enforced by cutting the string mid-word; type arrays and anyOf accepted; "pattern" made Ollama fail (500 "token repeat limit reached") and llama-server emit a runaway string.
