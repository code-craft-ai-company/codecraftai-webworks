# Captcha Spec

- **Tag:** `<mj-captcha>`
- **Class / file:** `Captcha` / `captcha.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Human verification field, Bot detection field
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-captcha>` is a human-verification form field that integrates with a pluggable
third-party CAPTCHA provider (reCAPTCHA v2/v3, hCaptcha, Cloudflare Turnstile,
or a custom adapter). It is form-associated, submitting the provider token under
a configured `name`. The component ensures that keyboard users always have an
accessible alternative challenge path and that the provider UI is never the sole
means of form completion.

## 2. When to use / when not to use
**Use** on registration, contact, and login forms where bot-prevention is required.
**Do not use** on every form — CAPTCHA adds friction for all users and should be
a last resort. **Do not use** without first confirming that the chosen provider
offers a WCAG AA accessible alternative challenge (audio, puzzle alternatives).

## 3. Anatomy
- **Provider container** (`part="provider-container"`) — the `<div>` into which the third-party CAPTCHA widget is mounted.
- **Status region** (`part="status"`) — live-region showing "Verifying…", "Verified", or error state.
- **Error message** (`part="error"`) — shown when the challenge fails or token expires.
- **Label** (`part="label"`) — optional visible label above the widget.
- **Help text** (`part="help"`) — optional hint (e.g., "Complete the security check to continue").
- **Fallback** (`part="fallback"`) — shown when the provider script fails to load.

## 4. Variants & modes
| Variant | `provider` value | Behavior |
|---------|-----------------|----------|
| reCAPTCHA v2 (checkbox) | `"recaptcha-v2"` | Explicit checkbox challenge widget |
| reCAPTCHA v3 (invisible) | `"recaptcha-v3"` | Invisible; token obtained on form submit |
| hCaptcha | `"hcaptcha"` | Checkbox challenge; WCAG-compliant audio alternative |
| Cloudflare Turnstile | `"turnstile"` | Managed challenge; invisible or widget mode |
| Custom | `"custom"` | Host provides a `providerAdapter` property |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `"captcha-token"` | yes | Form field name under which the token is submitted |
| `provider` | string | `""` | yes | Provider identifier; drives which adapter is used |
| `site-key` | string | `""` | yes | Provider-specific public site key |
| `theme` | `"light"\|"dark"\|"auto"` | `"auto"` | yes | Widget theme; `"auto"` follows `prefers-color-scheme` |
| `size` | `"normal"\|"compact"` | `"normal"` | yes | Widget size (providers that support it) |
| `label` | string | `""` | yes | Optional visible label above the widget |
| `help-text` | string | `""` | yes | Optional hint text |
| `error-message` | string | `""` | yes | Override the error message on failure |
| `required` | boolean | `true` | yes | Token must be present and valid for form submission |
| `disabled` | boolean | `false` | yes | Disables the widget; token submission blocked |
| `auto-execute` | boolean | `false` | yes | For invisible providers: execute the challenge immediately on connect |
| `token-expiry` | number | `120` | yes | Seconds after which the token is considered expired (provider-agnostic guard) |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `token` | string | Read-only; the current valid token string returned by the provider (`""` if none) |
| `verified` | boolean | Read-only; `true` when a non-expired token is present |
| `providerAdapter` | `CaptchaProviderAdapter` | Pluggable adapter object; used when `provider="custom"` |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

`CaptchaProviderAdapter` interface:
```
{
  load(container: HTMLElement, options: object): Promise<void>;
  execute(): Promise<string>;   // returns token
  reset(): void;
  destroy(): void;
}
```

## 7. Slots
| Slot | Description |
|------|-------------|
| `fallback` | Content shown when the provider script fails to load (e.g., a message directing the user to contact support) |
| `verified-message` | Content shown after successful verification (replaces the widget if desired) |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-verified` | `{ token: string }` | yes | no | Fires when the provider returns a valid token |
| `mj-expired` | `{}` | yes | no | Fires when the token expires; `token` is cleared |
| `mj-error` | `{ code: string, message: string }` | yes | no | Fires on provider error (network failure, invalid site key, etc.) |
| `mj-reset` | `{}` | yes | no | Fires when the widget is reset (token cleared, challenge ready again) |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when reportValidity finds the field invalid |

## 9. CSS parts & custom properties
**Parts:** `provider-container`, `status`, `error`, `label`, `help`, `fallback`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-captcha-container-min-height` | `78px` | Minimum height for the provider widget |
| `--mj-captcha-status-color` | `--mj-color-text-success` | Color of the "Verified" status text |
| `--mj-captcha-error-color` | `--mj-color-text-error` | Error message color |
| `--mj-captcha-label-color` | `--mj-color-text-default` | Label text color |

Note: the third-party widget itself is rendered in an `<iframe>` by providers and
cannot be styled via CSS parts. The `theme` attribute passes the appropriate
theme setting to the provider SDK.

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Idle (not yet verified) | Provider widget shown | `aria-invalid` not set; `aria-required` set if `required` |
| Loading | Widget container shows a skeleton | `aria-busy="true"` on container |
| Verified | Status shows "Verified ✓"; widget may collapse | `aria-live` announces "Verification successful" |
| Expired | Status shows "Verification expired"; widget resets | `aria-live` announces "Verification expired, please try again" |
| Error | Error message shown; widget may offer retry | `aria-live="assertive"` announces the error |
| Invalid (form submitted without token) | Error message shown | `aria-invalid="true"` on container |
| Disabled | Widget hidden; token submission blocked | `aria-disabled="true"` |
| Fallback (script failed) | Fallback slot shown | — |

## 11. Behavior & interactions
- On `connectedCallback`, the component loads the provider SDK script
  asynchronously (if not already present in the page). Script loading is
  idempotent — if the SDK script tag already exists the component waits for its
  load event.
- After the SDK loads, `providerAdapter.load(container, { siteKey, theme, size })`
  is called to mount the widget into `provider-container`.
- When the provider returns a token, `mj-verified` fires, `token` is set, and
  `ElementInternals` value is updated.
- Token expiry: a timer is set for `token-expiry` seconds. On expiry, `mj-expired`
  fires, `token` is cleared, and `ElementInternals` value is cleared.
- For invisible providers (`recaptcha-v3`, invisible Turnstile): `execute()` is
  called when the enclosing `<form>` fires a `submit` event (the component
  intercepts the event, calls `execute()`, awaits the token, then allows the
  form to submit).
- `reset()` can be called programmatically to clear the token and reset the widget.
- If the provider script fails to load after 10 seconds, the fallback slot is
  shown.
- `disabled` prevents the widget from being interacted with and clears any
  existing token.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Move focus into the provider widget's iframe (browser-managed) |
| `Shift+Tab` | Move focus backwards out of the widget |
| Within the widget | Provider-managed (checkbox, audio challenge, etc.) |

The component itself has no custom keyboard handling beyond focus management.
It must never add interactions that prevent keyboard users from reaching and
completing the challenge.

## 13. Accessibility
- The `provider-container` has `aria-label="Security verification"` (localizable)
  and `role="group"`.
- The status region has `role="status"` (polite) for verification/expiry messages
  and `role="alert"` (assertive) for errors.
- `aria-busy="true"` is set on the container while the SDK loads.
- `aria-invalid="true"` is set on the container when the form is submitted
  without a valid token.
- `aria-required="true"` on the container when `required` is set.
- The component documents that the chosen provider MUST offer a WCAG AA
  accessible alternative challenge (audio CAPTCHA or alternative challenge).
  hCaptcha and reCAPTCHA v2 both provide audio alternatives; the component does
  not suppress or wrap these — they are rendered inside the provider iframe.
- Fallback slot must provide an accessible alternative path for users unable to
  complete the challenge (e.g., a phone number or email address).

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Submits the provider token string as `name`/`value` in `FormData`.
- `required` validation: `valueMissing` when `token` is empty (no verification
  completed) or `customError` when the token has expired.
- Custom validity message: "Please complete the security verification." (localizable).
- Form reset clears the token and calls `providerAdapter.reset()`.
- For invisible providers, the component listens to `form submit` events and
  intercepts them to call `execute()` before the form is submitted.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- `label`, `help-text`, `error-message`, status messages ("Verifying", "Verified",
  "Verification expired"), and the group `aria-label` are all localizable via
  the shared localization hook.
- Provider widget language is set via the provider SDK's own locale option,
  derived from `document.documentElement.lang`.
- RTL: the label and help text align to the correct side; the provider widget's
  RTL support is provider-dependent and cannot be guaranteed.

## 16. Progressive enhancement / SSR
- Server renders a plain description: "This form is protected against automated
  submissions. JavaScript is required to complete verification."
- Without script, the CAPTCHA cannot function. The form should include a
  server-side fallback (e.g., a honeypot field or rate-limiting) rather than
  blocking submission entirely.
- On upgrade, the component mounts the provider SDK and widget.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Form-association helper** (§6).
- **Live-region service** (§6) — status and error announcements.
- **Localization hook** (§6).
- **Third-party CAPTCHA SDK** — loaded asynchronously at runtime; not bundled.

## 18. Edge cases & error handling
- SDK script fails to load (network error, ad-blocker): after the timeout, the
  fallback slot is shown; `mj-error` fires with `code: "sdk-load-failure"`.
- Invalid `site-key`: provider returns an error callback; `mj-error` fires; the
  widget shows the provider's own error; a console error is also emitted.
- `token-expiry` set to 0: the token never self-expires (the component does not
  start the timer); the provider's own expiry still applies.
- Multiple `<mj-captcha>` on the same page: each mounts its own widget using
  the SDK's multi-widget API if available; if not, only the first is functional
  and a console warning is emitted.
- `provider` changed at runtime: existing widget is destroyed, the new provider
  is loaded, and a new widget is mounted.
- Invisible provider form intercept: if `execute()` takes longer than 5 seconds,
  an error is emitted and the form submission is aborted.

## 19. Acceptance criteria
- [ ] Provider SDK loads asynchronously; widget mounts in `provider-container`.
- [ ] `mj-verified` fires with token when provider confirms; `ElementInternals` value updated.
- [ ] Token expiry timer fires `mj-expired`; token cleared; `mj-invalid` fires on subsequent `reportValidity`.
- [ ] `mj-error` fires on SDK load failure; fallback slot is shown.
- [ ] `required` + no token: `reportValidity()` sets `aria-invalid` and shows error message.
- [ ] Form reset calls `providerAdapter.reset()` and clears the token.
- [ ] Invisible provider: form submit is intercepted; `execute()` called; token obtained before submission proceeds.
- [ ] Status region announces "Verification successful" politely and errors assertively.
- [ ] `theme="auto"` applies correct theme based on `prefers-color-scheme`.
- [ ] `disabled` hides the widget and blocks token submission.
- [ ] Custom adapter via `providerAdapter` property works correctly with the `CaptchaProviderAdapter` interface.
- [ ] axe audit passes with zero violations (excluding provider iframe content).

## 20. Open questions
- Should the component support a `mock` mode for testing environments that bypasses the provider and injects a fake token?
- Should the fallback slot be shown in addition to or instead of the widget on error?
- Should `token-expiry` be auto-derived from the provider's callback rather than a fixed timer?
