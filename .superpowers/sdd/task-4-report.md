# Task 4 Report — Capacitor Install + Config + Android Scaffold

**Date:** 2026-06-29  
**Branch:** feat/mobile-capacitor  
**Status:** DONE

---

## 1. Versions pinned

| Package | Version |
|---|---|
| `@capacitor/core` | 6.2.1 |
| `@capacitor/cli` | 6.2.1 |
| `@capacitor/android` | 6.2.1 |
| `@capacitor/preferences` | 6.0.4 |
| `@capacitor-mlkit/barcode-scanning` | **6.2.0** (NOT latest 8.1.0 — pinned to `^6` because v8 requires `@capacitor/core>=8.0.0`) |

Note: `@capacitor-mlkit/barcode-scanning@^6` must be pinned explicitly. Default (`*`) resolves v8.1.0 which ERESOLVE-fails against Capacitor v6.

---

## 2. Files changed / created

| File | Action | Notes |
|---|---|---|
| `frontend/package.json` | Modified | Added Capacitor deps to `dependencies`; added `build:native` and `cap:sync` scripts |
| `frontend/package-lock.json` | Modified | Updated by npm install |
| `frontend/src/platform.js` | Modified | Added `/* @vite-ignore */` to dynamic import |
| `frontend/vite.config.js` | Modified | Added `isNativeBuild` flag, `nativeIndexHtml()` plugin, conditional `build` + `base` |
| `frontend/capacitor.config.ts` | Created | appId, appName, webDir=dist, androidScheme=https, CapacitorHttp |
| `frontend/index.native.html` | Created | Clean SPA shell for native entry (referenced by nativeIndexHtml plugin) |
| `frontend/.gitignore` | Created | `dist/`, `android/app/build/`, `android/.gradle/`, `android/local.properties` |
| `frontend/android/` | Created (scaffold) | Via `npx cap add android` |

---

## 3. Build / test results

### Web build (`npm run build`)

```
vite v6.4.2 building for production...
✓ 215 modules transformed.
../supplycore/public/frontend/index.css        60.69 kB
../supplycore/public/frontend/index.js        571.90 kB
../supplycore/public/frontend/chunks/...
✓ built in 3.35s
PWA v1.3.0 — generateSW — precache 11 entries
../supplycore/public/frontend/sw.js
```
**GREEN.** Output dir and base unchanged (`/assets/supplycore/frontend/`).

### Unit tests (`npm run test:unit`)

```
✓ tests/platform.spec.js (2 tests) 11ms
✓ tests/api-dualmode.spec.js (2 tests) 37ms
Test Files  2 passed (2)
     Tests  4 passed (4)
```
**ALL 4 PASS.**

### Native build (`npm run build:native`)

```
CAP_BUILD=1 NODE_OPTIONS=--experimental-global-webcrypto vite build
vite v6.4.2 building for production...
✓ 215 modules transformed.
dist/index.css    60.69 kB
dist/index.js    572.01 kB
dist/chunks/...
✓ built in 3.32s
PWA v1.3.0 — generateSW — precache 11 entries
dist/sw.js
```
`nativeIndexHtml` plugin generated `dist/index.html` with relative `./index.js` + `./index.css` references.
Chunk imports verified relative (`"./chunks/vue-vendor-...js"`).
No absolute `/assets/supplycore/...` paths in JS bundles.
**GREEN.**

### Android scaffold + cap sync

```
npx cap add android
✔ Adding native android project in android in 36.09ms
✔ add in 36.53ms
[success] android platform added!

npx cap sync android
✔ Copying web assets from dist to android/app/src/main/assets/public in 30.95ms
✔ Creating capacitor.config.json in android/app/src/main/assets in 1.10ms
✔ copy android in 47.41ms
✔ Updating Android plugins in 6.68ms
[info] Found 2 Capacitor plugins for android:
       @capacitor-mlkit/barcode-scanning@6.2.0
       @capacitor/preferences@6.0.4
✔ update android in 53.82ms
[info] Sync finished in 0.122s
```
**SUCCEEDED.** Android SDK/Java NOT present on this machine (no ANDROID_HOME, no `~/Android/Sdk`), but `npx cap add android` scaffolds the project files without needing the SDK. `cap sync` also succeeds (it only copies web assets + writes config JSON — gradle/build steps are deferred). Full Gradle build must be done on a machine with Android Studio (Task 11).

---

## 4. Notable decisions / deviations from brief

1. **`build:native` script required `NODE_OPTIONS=--experimental-global-webcrypto`** — Node 18 doesn't expose `crypto` globally by default; the existing `build` script already uses this flag; added it to `build:native` too. Brief omitted it.

2. **`nativeIndexHtml` Vite plugin** — `cap sync` requires `dist/index.html`. The Vite build with `input: 'src/main.js'` produces JS/CSS but no HTML. Added a `closeBundle` plugin that generates a minimal `dist/index.html` (relative `./index.js` + `./index.css` refs). Also created `index.native.html` in frontend root as the source template.

3. **`@capacitor-mlkit/barcode-scanning` pinned to `^6.2.0`** — v8+ requires `@capacitor/core>=8`, incompatible with Capacitor 6. Pinned to v6.2.0 explicitly.

4. **PWA plugin still runs in native build** — VitePWA still generates `dist/sw.js` in native mode. This is harmless (Capacitor ignores SW in native context), and disabling it would require restructuring the plugins array more invasively.

---

## 5. Concerns / follow-up for Task 11

- `android/` scaffold is committed but **cannot build without Android SDK + Java**. Set up Android Studio on the build machine and run `cd frontend/android && ./gradlew assembleDebug`.
- PWA manifest icon paths in native SW remain absolute (`/assets/supplycore/frontend/icons/...`) — these are from the manifest config and are not used by Capacitor in native mode.

---

## 6. Post-review cleanup (2026-06-29)

**What changed:**
1. Deleted `frontend/index.native.html` — orphan file pointing to `./src/main.js` that would break Capacitor if used; the `nativeIndexHtml()` Vite plugin generates `dist/index.html` inline and never reads this file.
2. Added a 2-line comment above `nativeIndexHtml()` in `vite.config.js` explaining the HTML is generated inline because the Vite entry is `src/main.js` (not an HTML entry).
3. Moved `@capacitor/cli` from `dependencies` to `devDependencies` in `frontend/package.json` — it is a build-time CLI, not shipped in the bundle.

**Verification results:**

`npm run build:native`:
```
vite v6.4.2 building for production...
✓ 215 modules transformed.
dist/index.css    60.69 kB
dist/index.js    572.01 kB
dist/chunks/...
✓ built in 3.40s
PWA v1.3.0 — generateSW — precache 11 entries — dist/sw.js
```
`dist/index.html` present — references `./index.css` and `./index.js`. GREEN.

`npm run build` (web):
```
vite v6.4.2 building for production...
✓ 215 modules transformed.
../supplycore/public/frontend/index.css    60.69 kB
../supplycore/public/frontend/index.js    571.90 kB
✓ built in 3.35s
PWA v1.3.0 — generateSW — precache 11 entries — ../supplycore/public/frontend/sw.js
```
GREEN.

`npm run test:unit`:
```
✓ tests/platform.spec.js (2 tests) 31ms
✓ tests/api-dualmode.spec.js (2 tests) 39ms
Test Files  2 passed (2)
     Tests  4 passed (4)
```
ALL 4 PASS.
