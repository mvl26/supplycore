# Task 6 Report — Màn hình cấu hình server + đăng nhập (ServerLogin.vue)

## Files changed

- `frontend/src/api.js` — added exported `mobileLoginApi(serverUrl, usr, pwd)` in the Auth section, before `login()`. Uses raw `fetch` (not `request`) with `credentials:'omit'`, strips trailing slashes from serverUrl, returns `body.message`. Reuses module-private `parseFrappeError` for error extraction.

- `frontend/src/stores/auth.js` — added imports `mobileLoginApi` from `../api` and `setServerUrl, setToken` from `../platform`. Added `mobileLogin(serverUrl, usr, pwd)` action: calls `mobileLoginApi`, persists server URL + token via platform, sets `this.user`, sets `this.booted = true`, calls `useAccessStore().load(true)`. Returns boolean; sets `this.loginError` on failure.

- `frontend/src/mobile/ServerLogin.vue` — replaced stub with real form: server URL (`type="url"`), username (`autocapitalize="none"`), password (`type="password"`). Submit disabled until URL matches `^https?:\/\/.+` and both fields filled. On success routes to `/m/lookup`. Navy `#1F4E79` primary button. Vietnamese UI text, no emoji.

- `frontend/tests/mobile-login.spec.js` — 3 vitest unit tests for `mobileLoginApi`: (1) POSTs to correct URL, (2) strips trailing slash from serverUrl, (3) returns unwrapped `.message`. Written before implementation (TDD RED→GREEN).

## Test output

```
Tests  7 passed (7)   [3 new + 4 existing — all green]
```

TDD flow: tests ran RED (TypeError: mobileLoginApi is not a function × 3) before implementation; GREEN after.

## Build results

- `npm run build` (web): ✓ built in 3.42s
- `npm run build:native` (CAP_BUILD=1): ✓ built in 3.18s

Both builds produce `ServerLogin-Cujmofd9.js` (1.53 kB gzip 0.85 kB) — code-split correctly.

## Commit

`3b6f7fa` feat(mobile): màn hình cấu hình server + đăng nhập token

## Addendum — null-guard + 401 error-path test (2026-06-29)

### Changes

- `frontend/src/api.js` line 152: `return body.message` → `return body?.message` (null-guard for 2xx non-JSON responses where `body` is `null`).
- `frontend/tests/mobile-login.spec.js`: added 4th test `'rejects with parsed error message on 401 AuthenticationError'` — mocks `fetch` to return `{ ok:false, status:401, json: async () => ({ exc_type:'AuthenticationError', exception:'AuthenticationError: Bad credentials' }) }` and asserts `mobileLoginApi('https://x.com','u','p')` rejects with message containing `'Bad credentials'`. `parseFrappeError` strips the class-prefix via regex (`AuthenticationError: Bad credentials` → `Bad credentials`) and no ERROR_MAP rule matches, so `friendlyError` returns the text verbatim.

### Test output

```
 RUN  v2.1.9

 ✓ tests/platform.spec.js (2 tests) 28ms
 ✓ tests/api-dualmode.spec.js (2 tests) 30ms
 ✓ tests/mobile-login.spec.js (4 tests) 42ms

 Test Files  3 passed (3)
      Tests  8 passed (8)
   Start at  11:04:28
   Duration  473ms
```

### Build results

- `npm run build` (web): ✓ built in 3.36s
- `npm run build:native` (CAP_BUILD=1): ✓ built in 3.32s

(Chunk-size warning >500 kB is pre-existing, unrelated to this task.)

## Decisions / notes

- `api_secret` is never logged; it flows only into `setToken()` which writes to `@capacitor/preferences` (native-only, no web storage).
- `mobileLoginApi` is separate from `request()` because it runs pre-auth (no token yet, no CSRF), so it cannot share request infrastructure.
- The chunk-size warning (>500 kB) pre-existed and is unrelated to this task.
