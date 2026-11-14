/*
 * mjcaptcha.js
 *
 * <mj-captcha> -- pluggable CAPTCHA integration with provider adapter
 * pattern, form participation, token lifecycle, and accessibility.
 *
 * A provider is mounted whenever an adapter is available: the one assigned
 * to `providerAdapter`, or a built-in adapter for the `provider` attribute.
 * No built-in adapters ship yet, so `provider` alone ends in the fallback.
 *
 * Every mount gets a sequence number; results of a load or execute that was
 * superseded (provider changed, element removed) are ignored, and all
 * timers are cleared when a mount is cleaned up.
 *
 * Adapter interface: `load(container, options)` mounts the widget, where
 * options are `{ siteKey, theme, size, onVerify(token), onExpire(),
 * onError(error) }`. A visible widget the user solves reports the token
 * through `onVerify` whenever that happens (as the vendors' `callback` /
 * `expired-callback` / `error-callback` do); `execute()` (a Promise of the
 * token, raced against EXECUTE_TIMEOUT_MS) runs the challenge on demand:
 * after load with `auto-execute`, and on submit for invisible providers.
 * `reset()` and `destroy()` are optional.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-md);
}

.label {
  display: block;
  margin-bottom: var(--mj-space-1);
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text);
}
.label:empty { display: none; }

.provider-container {
  min-height: var(--mj-captcha-container-min-height, 78px);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.provider-container[aria-busy="true"]::before {
  content: "";
  display: block;
  width: 300px;
  height: 74px;
  background: var(--mj-bg-muted);
  border-radius: var(--mj-radius-md);
  animation: mj-pulse 1.5s ease-in-out infinite;
}
@keyframes mj-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status {
  margin-top: var(--mj-space-2);
  font-size: var(--mj-font-size-sm);
  display: none;
}
.status[data-visible] { display: block; }
.status[data-type="verified"] { color: var(--mj-color-success); }
.status[data-type="expired"] { color: var(--mj-color-warning); }
.status[data-type="error"] { color: var(--mj-color-danger); }

.verified-slot { display: none; }
.verified-slot[data-visible] { display: block; }

.fallback { display: none; }
.fallback[data-visible] { display: block; }

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .provider-container, .provider-container[data-disabled] { opacity: 0.55; pointer-events: none; }
@media (prefers-reduced-motion: reduce) {
  .provider-container[aria-busy="true"]::before { animation: none; }
}
`;

/* Providers whose challenge runs on form submit instead of in a widget. */
const INVISIBLE_PROVIDERS = ["recaptcha-v3", "turnstile"];

/* How long the provider SDK may take to load, and a challenge to answer. */
const LOAD_TIMEOUT_MS = 10000;
const EXECUTE_TIMEOUT_MS = 5000;

const DEFAULT_TOKEN_EXPIRY_SECONDS = 120;

export class MjCaptcha extends FormControlMixin(MjElement) {
  static tagName = "mj-captcha";
  static styles = STYLES;
  static watched = [
    "label", "help-text", "error-message", "provider", "site-key",
    "theme", "size", "required", "disabled", "auto-execute", "token-expiry"
  ];

  constructor() {
    super()
    this._initFormControl()

    this._token = ""
    this._verified = false

    /* The adapter assigned by the host, and the one currently mounted. */
    this._providerAdapter = null
    this._adapter = null

    /*
     * The `provider` value the current mount was made for, or null when
     * nothing was mounted since the last cleanup. The attribute is delivered
     * again after the first render; an unchanged value must not remount.
     */
    this._mountedProvider = null

    /* Incremented by every mount and cleanup; stale async results compare against it. */
    this._mountSerial = 0

    this._expiryTimer = null
    this._loadTimer = null
    this._executeTimer = null

    /*
     * The challenge in progress: its promise, and the { resolve, reject }
     * the widget callbacks settle it with (see _executeWithTimeout).
     */
    this._pendingExecution = null
    this._pendingExecute = null

    /* True while a held form submit waits for the challenge to finish. */
    this._submitHeld = false

    /* The form whose submit is intercepted, and the handler that was added. */
    this._watchedForm = null
    this._formSubmitHandler = null

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* Errors are shown once a submit attempt failed. */
    this._showErrors = false

    this._containerId = nextId("mjca-container")
    this._helpId = nextId("mjca-help")
    this._errorId = nextId("mjca-error")
    this._statusId = nextId("mjca-status")
  }

  render() {
    const markup = html`
      <div class="label" part="label"></div>
      <div
        class="provider-container"
        part="provider-container"
        id="${this._containerId}"
        role="group"
        aria-label="${t("mj.captcha.groupLabel")}"
        aria-busy="false"
      ></div>
      <div class="status" part="status" id="${this._statusId}" role="status" aria-live="polite"></div>
      <div class="verified-slot" part="verified-message" role="status" aria-live="polite"><slot name="verified-message"></slot></div>
      <div class="fallback" part="fallback" role="status">
        <slot name="fallback">
          <p>${t("mj.captcha.unavailable")}</p>
        </slot>
      </div>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._labelEl = this.$(".label")
    this._containerEl = this.$(".provider-container")
    this._statusEl = this.$(".status")
    this._verifiedEl = this.$(".verified-slot")
    this._verifiedSlot = this.$("slot[name='verified-message']")
    this._fallbackEl = this.$(".fallback")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")

    this._setFormValue(this._token)
    this._syncAll()
    this._mountProvider()

    this.listen(this, "invalid", this._onInvalid.bind(this))
    return
  }

  /* The form is watched on every connect; teardown removes the handler. */
  onConnected() {
    this._watchForm()
    return
  }

  onDisconnected() {
    this._cleanupProvider()
    this._unwatchForm()
    this._clearExpiryTimer()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._containerEl === undefined || this._containerEl === null) {
      return
    }
    if (name === "provider" && (newValue || "") !== this._mountedProvider) {
      this._cleanupProvider()
      this._mountProvider()
      this._unwatchForm()
      this._watchForm()
    }
    if (name === "required" || name === "provider") {
      this._refreshValidity()
      this._renderValidity(false)
    }
    this._syncAll()
    return
  }

  /* The control is disabled by its own attribute or by a disabled fieldset. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  _isInvisibleProvider() {
    const provider = this.getAttribute("provider") || ""
    const invisible = INVISIBLE_PROVIDERS.indexOf(provider) >= 0
    return invisible
  }

  _syncAll() {
    const label = this.getAttribute("label") || ""
    const helpText = this.getAttribute("help-text") || ""
    const disabled = this._isDisabled()

    this._labelEl.textContent = label
    this._helpEl.textContent = helpText
    /*
     * `aria-required` is not allowed on the group role, so the required
     * state is not put on the container: it is enforced through validity
     * (valueMissing, reportValidity()) and the visible label should say
     * that the verification is required.
     */
    this._containerEl.setAttribute("aria-disabled", disabled === true ? "true" : "false")
    this._containerEl.toggleAttribute("data-disabled", disabled === true)
    this._updateDescribedBy()
    return
  }

  _updateDescribedBy() {
    const ids = []
    if (this._helpEl.textContent.length > 0) {
      ids.push(this._helpId)
    }
    if (this._errorEl.hasAttribute("data-visible") === true) {
      ids.push(this._errorId)
    }
    if (ids.length > 0) {
      this._containerEl.setAttribute("aria-describedby", ids.join(" "))
    } else {
      this._containerEl.removeAttribute("aria-describedby")
    }
    return
  }

  /* ----- provider lifecycle ----- */

  /*
   * Mount the assigned adapter, or the built-in one for `provider`. A
   * `provider` with no adapter shows the fallback; with neither, nothing is
   * mounted. Any fallback or error from an earlier attempt is cleared first.
   */
  _mountProvider() {
    const provider = this.getAttribute("provider") || ""
    const siteKey = this.getAttribute("site-key") || ""
    const theme = this._resolveTheme()
    const size = this.getAttribute("size") || "normal"
    const autoExecute = this.hasAttribute("auto-execute")

    this._mountSerial = this._mountSerial + 1
    const serial = this._mountSerial
    this._mountedProvider = provider

    this._fallbackEl.removeAttribute("data-visible")
    this._clearStatus()

    let adapter = this._providerAdapter
    if (adapter === null || adapter === undefined) {
      adapter = provider.length > 0 ? this._getBuiltinAdapter(provider) : null
    }

    if (adapter === null || adapter === undefined) {
      this._containerEl.setAttribute("aria-busy", "false")
      if (provider.length > 0) {
        this._showFallback("sdk-load-failure")
      }
      return
    }

    this._containerEl.setAttribute("aria-busy", "true")
    this._loadTimer = setTimeout(() => {
      this._loadTimer = null
      if (serial === this._mountSerial) {
        this._showFallback("sdk-load-failure")
      }
    }, LOAD_TIMEOUT_MS)

    const options = {
      siteKey: siteKey,
      theme: theme,
      size: size,
      onVerify: (token) => {
        if (serial === this._mountSerial) {
          this._acceptToken(token)
          this._settlePendingExecute(token, null)
        }
        return
      },
      onExpire: () => {
        if (serial === this._mountSerial && this._verified === true) {
          this._clearExpiryTimer()
          this._onExpired()
        }
        return
      },
      onError: (error) => {
        if (serial !== this._mountSerial) {
          return
        }
        /* A challenge in progress reports the failure itself (execute-failed). */
        const failure = error instanceof Error ? error : new Error(error !== null && error !== undefined ? String(error) : t("mj.captcha.providerFailed"))
        if (this._settlePendingExecute(null, failure) === false) {
          this._reportProviderError(failure)
        }
        return
      }
    }

    let loading = null
    try {
      loading = Promise.resolve(adapter.load(this._containerEl, options))
    } catch (error) {
      loading = Promise.reject(error)
    }

    loading
      .then(() => {
        if (serial !== this._mountSerial) {
          /* Superseded while loading: release what this load created. */
          this._destroyAdapter(adapter)
          return null
        }
        this._clearLoadTimer()
        this._containerEl.setAttribute("aria-busy", "false")
        this._fallbackEl.removeAttribute("data-visible")
        this._adapter = adapter

        let result = null
        if (autoExecute === true) {
          result = this._executeWithTimeout()
        }
        return result
      })
      .then((token) => {
        if (serial === this._mountSerial && token !== null && token !== undefined) {
          this._acceptToken(token)
        }
      })
      .catch((error) => {
        if (serial !== this._mountSerial) {
          return
        }
        this._clearLoadTimer()
        this._reportProviderError(error)
      })
    return
  }

  /* A failed load or auto-execute, or an error the widget reported. */
  _reportProviderError(error) {
    const message = error !== null && error !== undefined && error.message ? error.message : t("mj.captcha.providerFailed")
    console.error("[mj-captcha] provider error:", error)
    this._showError(message)
    this.emit("mj-error", { code: "provider-error", message: message })
    return
  }

  /* Built-in provider adapters; none are bundled yet. */
  _getBuiltinAdapter(provider) {
    return null
  }

  _destroyAdapter(adapter) {
    if (adapter !== null && adapter !== undefined && typeof adapter.destroy === "function") {
      try {
        adapter.destroy()
      } catch (error) {
        console.error("[mj-captcha] adapter destroy failed:", error)
      }
    }
    return
  }

  _clearLoadTimer() {
    if (this._loadTimer !== null) {
      clearTimeout(this._loadTimer)
      this._loadTimer = null
    }
    return
  }

  _clearExecuteTimer() {
    if (this._executeTimer !== null) {
      clearTimeout(this._executeTimer)
      this._executeTimer = null
    }
    return
  }

  _clearExpiryTimer() {
    if (this._expiryTimer !== null) {
      clearTimeout(this._expiryTimer)
      this._expiryTimer = null
    }
    return
  }

  /* Unmount: invalidate pending results, clear timers, destroy the adapter. */
  _cleanupProvider() {
    this._mountSerial = this._mountSerial + 1
    this._mountedProvider = null
    this._clearLoadTimer()
    this._clearExecuteTimer()
    this._pendingExecution = null
    this._pendingExecute = null
    this._submitHeld = false

    if (this._adapter !== null && this._adapter !== undefined) {
      this._destroyAdapter(this._adapter)
      this._adapter = null
    }
    if (this._containerEl !== undefined && this._containerEl !== null) {
      this._containerEl.textContent = ""
      this._containerEl.setAttribute("aria-busy", "false")
    }
    return
  }

  /*
   * Run the challenge, failing after EXECUTE_TIMEOUT_MS. It settles with
   * whatever comes first: execute()'s token, a token or error the widget
   * reports through `onVerify` / `onError`, or the timeout.
   */
  _executeWithTimeout() {
    const adapter = this._adapter
    if (this._pendingExecution !== null) {
      /* One challenge at a time: a second caller waits for the same one. */
      return this._pendingExecution
    }
    this._clearExecuteTimer()

    const timeout = new Promise((resolve, reject) => {
      this._executeTimer = setTimeout(() => {
        this._executeTimer = null
        reject(new Error("execute timeout"))
      }, EXECUTE_TIMEOUT_MS)
    })

    const reported = new Promise((resolve, reject) => {
      this._pendingExecute = { resolve: resolve, reject: reject }
    })

    let started = null
    try {
      if (adapter === null || adapter === undefined || typeof adapter.execute !== "function") {
        throw new Error("the provider adapter has no execute()")
      }
      started = Promise.resolve(adapter.execute())
    } catch (error) {
      started = Promise.reject(error)
    }

    const execution = Promise.race([started, reported, timeout])
      .finally(() => {
        if (this._pendingExecution === execution) {
          this._clearExecuteTimer()
          this._pendingExecution = null
          this._pendingExecute = null
        }
      })
    this._pendingExecution = execution
    return execution
  }

  /*
   * Settle the challenge in progress with a token or an error. Returns true
   * when one was waiting.
   */
  _settlePendingExecute(token, error) {
    const pending = this._pendingExecute
    if (pending === null) {
      return false
    }
    this._pendingExecute = null
    if (error !== null) {
      pending.reject(error)
    } else {
      pending.resolve(token)
    }
    return true
  }

  /*
   * A token from execute() or from the widget's `onVerify`. The same token
   * reported both ways verifies once; an empty result after the widget has
   * already verified keeps that verification.
   */
  _acceptToken(token) {
    const text = token !== null && token !== undefined ? String(token) : ""
    const alreadyAccepted = this._verified === true && (text === this._token || text.length === 0)
    if (alreadyAccepted === false) {
      this._onVerified(text)
    }
    return
  }

  _resolveTheme() {
    const theme = this.getAttribute("theme") || "auto"
    let resolved = theme
    if (theme === "auto") {
      resolved = window.matchMedia("(prefers-color-scheme: dark)").matches === true ? "dark" : "light"
    }
    return resolved
  }

  /* ----- form interception ----- */

  _watchForm() {
    if (this._watchedForm !== null) {
      return
    }
    const owner = this.form !== null && this.form !== undefined ? this.form : this.closest("form")
    if (owner === null) {
      return
    }

    this._watchedForm = owner
    this._formSubmitHandler = this._onFormSubmit.bind(this)
    owner.addEventListener("submit", this._formSubmitHandler, { capture: true })
    this.onTeardown(() => {
      this._unwatchForm()
    })
    return
  }

  /* Remove exactly the handler that was added. */
  _unwatchForm() {
    if (this._watchedForm !== null && this._formSubmitHandler !== null) {
      this._watchedForm.removeEventListener("submit", this._formSubmitHandler, { capture: true })
    }
    this._watchedForm = null
    this._formSubmitHandler = null
    return
  }

  /*
   * Gate the submit of the owning form. A verified captcha lets it through.
   * An invisible provider runs its challenge first and then re-submits with
   * the original submitter; a visible one blocks the submit of a required,
   * unverified captcha and shows why (this also covers `novalidate` forms,
   * where constraint validation does not stop the submit).
   */
  _onFormSubmit(event) {
    if (this._verified === true || this._isDisabled() === true) {
      return
    }

    const form = this._watchedForm
    const submitter = event.submitter !== undefined ? event.submitter : null

    if (this._isInvisibleProvider() === false) {
      if (this.hasAttribute("required") === true) {
        event.preventDefault()
        event.stopPropagation()
        this._showErrors = true
        this._refreshValidity()
        this._renderValidity(true)
      }
      return
    }

    event.preventDefault()
    event.stopPropagation()

    if (this._submitHeld === true) {
      /* A submit is already held; it is re-sent once the challenge ends. */
      return
    }

    if (this._adapter === null || this._adapter === undefined) {
      const message = t("mj.captcha.notReady")
      this._showError(message)
      this.emit("mj-error", { code: "not-ready", message: message })
      return
    }

    const serial = this._mountSerial
    this._submitHeld = true
    this._setStatus("verifying", t("mj.captcha.verifying"))

    this._executeWithTimeout()
      .then((token) => {
        if (serial !== this._mountSerial) {
          return
        }
        this._submitHeld = false
        this._acceptToken(token)
        if (this._verified === false) {
          /* No token: re-submitting would only run the challenge again. */
          const message = t("mj.captcha.verificationFailed")
          this._showError(message)
          this.emit("mj-error", { code: "execute-failed", message: message })
          return
        }
        if (form !== null && typeof form.requestSubmit === "function") {
          const stillOwned = submitter !== null && submitter.form === form
          if (stillOwned === true) {
            form.requestSubmit(submitter)
          } else {
            form.requestSubmit()
          }
        }
      })
      .catch((error) => {
        if (serial !== this._mountSerial) {
          return
        }
        this._submitHeld = false
        const message = error !== null && error !== undefined && error.message ? error.message : t("mj.captcha.verificationFailed")
        console.error("[mj-captcha] execute failed:", error)
        this._showError(message)
        this.emit("mj-error", { code: "execute-failed", message: message })
      })
    return
  }

  /* ----- token lifecycle ----- */

  _onVerified(token) {
    this._token = token !== null && token !== undefined ? String(token) : ""
    this._verified = this._token.length > 0
    this._setFormValue(this._token)
    this._showErrors = false
    this._renderValidity(false)

    if (this._verified === false) {
      return
    }

    /* Custom verified content replaces the built-in status text. */
    const custom = this._verifiedSlot.assignedNodes({ flatten: true }).length > 0
    this._verifiedEl.toggleAttribute("data-visible", custom === true)
    if (custom === true) {
      /* The slot wrapper is itself a polite live region. */
      this._clearStatus()
    } else {
      this._setStatus("verified", t("mj.captcha.verified"))
    }
    this.emit("mj-verified", { token: this._token })

    let expirySeconds = parseInt(this.getAttribute("token-expiry") || String(DEFAULT_TOKEN_EXPIRY_SECONDS), 10)
    if (Number.isNaN(expirySeconds) === true) {
      expirySeconds = DEFAULT_TOKEN_EXPIRY_SECONDS
    }
    this._clearExpiryTimer()
    if (expirySeconds > 0) {
      this._expiryTimer = setTimeout(() => {
        this._expiryTimer = null
        this._onExpired()
      }, expirySeconds * 1000)
    }
    return
  }

  _onExpired() {
    this._token = ""
    this._verified = false
    this._setFormValue("")
    this._verifiedEl.removeAttribute("data-visible")
    this._setStatus("expired", t("mj.captcha.expired"))
    this.emit("mj-expired", {})
    return
  }

  _setStatus(type, message) {
    this._statusEl.setAttribute("role", type === "error" ? "alert" : "status")
    this._statusEl.setAttribute("aria-live", type === "error" ? "assertive" : "polite")
    this._statusEl.setAttribute("data-visible", "")
    this._statusEl.setAttribute("data-type", type)
    this._statusEl.textContent = message
    return
  }

  _clearStatus() {
    this._statusEl.removeAttribute("data-visible")
    this._statusEl.removeAttribute("data-type")
    this._statusEl.setAttribute("role", "status")
    this._statusEl.setAttribute("aria-live", "polite")
    this._statusEl.textContent = ""
    return
  }

  _showError(message) {
    this._containerEl.setAttribute("aria-busy", "false")
    const override = this.getAttribute("error-message") || ""
    this._setStatus("error", override.length > 0 ? override : message)
    return
  }

  _showFallback(code) {
    this._containerEl.setAttribute("aria-busy", "false")
    this._fallbackEl.setAttribute("data-visible", "")
    this.emit("mj-error", { code: code, message: t("mj.captcha.providerFailed") })
    return
  }

  /* ----- validation ----- */

  /* A failed checkValidity() / reportValidity() / form submit. */
  _onInvalid(event) {
    this._showErrors = true
    this._renderValidity(true)
    return
  }

  _renderValidity(announce) {
    const message = this.validationMessage
    const invalid = message.length > 0 && this._showErrors === true

    if (invalid === true) {
      const override = this.getAttribute("error-message") || ""
      const displayMessage = override.length > 0 ? override : message
      this._errorEl.textContent = displayMessage
      this._errorEl.setAttribute("data-visible", "")
      this._containerEl.setAttribute("aria-invalid", "true")
      if (announce === true) {
        this.emit("mj-invalid", { validationMessage: displayMessage })
      }
    } else {
      this._errorEl.textContent = ""
      this._errorEl.removeAttribute("data-visible")
      this._containerEl.removeAttribute("aria-invalid")
    }
    this._updateDescribedBy()
    return
  }

  /*
   * An unverified (or expired) required captcha is valueMissing. Invisible
   * providers are the exception: their challenge only runs once the submit
   * event fires, which constraint validation would prevent, so the submit
   * interceptor enforces them instead.
   */
  _refreshValidity() {
    if (this._internals === null || this._internals === undefined) {
      return
    }
    const required = this.hasAttribute("required")
    const gatedOnSubmit = this._isInvisibleProvider()
    if (required === true && gatedOnSubmit === false && (this._token.length === 0 || this._verified === false)) {
      const message = this.getAttribute("required-message") || t("mj.captcha.required")
      const anchor = this._validationAnchor()
      if (anchor !== null && anchor !== undefined) {
        this._internals.setValidity({ valueMissing: true }, message, anchor)
      } else {
        this._internals.setValidity({ valueMissing: true }, message)
      }
    } else {
      this._internals.setValidity({})
    }
    return
  }

  /* Only a focusable element inside the provider widget can anchor the bubble. */
  _validationAnchor() {
    let anchor = null
    if (this._containerEl !== undefined && this._containerEl !== null) {
      anchor = this._containerEl.querySelector("iframe, button, input, [tabindex]")
    }
    return anchor
  }

  onFormReset(initial) {
    this._token = ""
    this._verified = false
    this._showErrors = false
    this._setFormValue("")
    this._clearExpiryTimer()
    if (this._adapter !== null && this._adapter !== undefined && typeof this._adapter.reset === "function") {
      this._adapter.reset()
    }
    if (this._statusEl !== undefined && this._statusEl !== null) {
      this._clearStatus()
      this._verifiedEl.removeAttribute("data-visible")
      this._renderValidity(false)
    }
    this.emit("mj-reset", {})
    return
  }

  /* A restored token may already have expired; start unverified. */
  onFormRestore(state) {
    this.onFormReset("")
    return
  }

  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    if (this._containerEl !== undefined && this._containerEl !== null) {
      this._syncAll()
    }
    return
  }

  /* ----- public API ----- */

  get token() {
    return this._token
  }

  get verified() {
    return this._verified
  }

  get providerAdapter() {
    return this._providerAdapter
  }

  set providerAdapter(adapter) {
    this._providerAdapter = adapter !== undefined ? adapter : null
    if (this._containerEl !== undefined && this._containerEl !== null) {
      this._cleanupProvider()
      this._mountProvider()
    }
    return
  }

  checkValidity() {
    this._refreshValidity()
    const valid = super.checkValidity()
    return valid
  }

  reportValidity() {
    this._refreshValidity()
    const valid = super.reportValidity()
    return valid
  }

  reset() {
    this.onFormReset("")
    return
  }

  focus(options) {
    if (this._containerEl !== undefined && this._containerEl !== null) {
      const focusable = this._containerEl.querySelector("iframe, button, input, [tabindex]")
      if (focusable !== null) {
        focusable.focus(options)
      }
    }
    return
  }
}
