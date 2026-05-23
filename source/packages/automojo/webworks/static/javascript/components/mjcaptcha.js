/*
 * mjcaptcha.js
 *
 * <mj-captcha> -- pluggable CAPTCHA integration with provider adapter
 * pattern, form participation, token lifecycle, and accessibility.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";

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
  min-height: 78px;
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

.fallback { display: none; }
.fallback[data-visible] { display: block; }

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .provider-container { opacity: 0.55; pointer-events: none; }
`;

export class MjCaptcha extends FormControlMixin(MjElement) {
  static tagName = "mj-captcha";
  static styles = STYLES;
  static watched = [
    "label", "help-text", "error-message", "provider", "site-key",
    "theme", "size", "required", "disabled", "auto-execute", "token-expiry"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._token = "";
    this._verified = false;
    this._expiryTimer = null;
    this._providerAdapter = null;
    this._formSubmitHandler = null;
    this._containerId = nextId("mjca-container");
    this._helpId = nextId("mjca-help");
    this._errorId = nextId("mjca-error");
    this._statusId = nextId("mjca-status");
  }

  render() {
    const label = this.getAttribute("label") || "";
    const helpText = this.getAttribute("help-text") || "";
    const markup = `
      <div class="label" part="label">${label}</div>
      <div
        class="provider-container"
        part="provider-container"
        id="${this._containerId}"
        role="group"
        aria-label="Security verification"
        aria-busy="false"
      ></div>
      <div class="status" part="status" id="${this._statusId}" role="status" aria-live="polite"></div>
      <div class="fallback" part="fallback" role="status">
        <slot name="fallback">
          <p>Security verification is not available. Please try again later or contact support.</p>
        </slot>
      </div>
      <slot name="verified-message" hidden></slot>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}">${helpText}</span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `;
    return markup;
  }

  afterRender() {
    this._labelEl = this.$(".label");
    this._containerEl = this.$(".provider-container");
    this._statusEl = this.$(".status");
    this._fallbackEl = this.$(".fallback");
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");

    this._syncAll();
    this._mountProvider();
    this._watchForm();
    return;
  }

  onConnected() {
    this._watchForm();
    return;
  }

  onDisconnected() {
    this._cleanupProvider();
    this._unwatchForm();
    if (this._expiryTimer !== null) {
      clearTimeout(this._expiryTimer);
      this._expiryTimer = null;
    }
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._containerEl === undefined) {
      return;
    }
    if (name === "provider" && oldValue !== newValue) {
      this._cleanupProvider();
      this._mountProvider();
    }
    this._syncAll();
    return;
  }

  _syncAll() {
    const label = this.getAttribute("label") || "";
    const helpText = this.getAttribute("help-text") || "";
    const required = this.hasAttribute("required");

    if (this._labelEl !== undefined) {
      this._labelEl.textContent = label;
    }
    if (this._helpEl !== undefined) {
      this._helpEl.textContent = helpText;
    }
    if (this._containerEl !== undefined) {
      this._containerEl.setAttribute("aria-required", required ? "true" : "false");
    }
    return;
  }

  _mountProvider() {
    const provider = this.getAttribute("provider") || "";
    const siteKey = this.getAttribute("site-key") || "";
    const theme = this._resolveTheme();
    const size = this.getAttribute("size") || "normal";
    const autoExecute = this.hasAttribute("auto-execute");

    if (provider.length === 0) {
      return;
    }

    this._containerEl.setAttribute("aria-busy", "true");

    const adapter = this._providerAdapter || this._getBuiltinAdapter(provider);
    if (adapter === null) {
      this._showFallback("sdk-load-failure");
      return;
    }

    const loadTimeout = setTimeout(() => {
      this._showFallback("sdk-load-failure");
    }, 10000);

    adapter.load(this._containerEl, { siteKey, theme, size })
      .then(() => {
        clearTimeout(loadTimeout);
        this._containerEl.setAttribute("aria-busy", "false");
        this._adapter = adapter;

        if (autoExecute) {
          return adapter.execute();
        }
        return null;
      })
      .then((token) => {
        if (token !== null && token !== undefined) {
          this._onVerified(token);
        }
      })
      .catch((err) => {
        clearTimeout(loadTimeout);
        console.error("[mj-captcha] provider error:", err);
        this._showError(err.message || "Provider failed to load.");
        this.emit("mj-error", { code: "provider-error", message: err.message || "Provider failed to load." });
      });
    return;
  }

  _getBuiltinAdapter(provider) {
    return null;
  }

  _cleanupProvider() {
    if (this._adapter !== undefined && this._adapter !== null) {
      this._adapter.destroy();
      this._adapter = null;
    }
    if (this._containerEl !== undefined) {
      this._containerEl.innerHTML = "";
    }
    return;
  }

  _resolveTheme() {
    const theme = this.getAttribute("theme") || "auto";
    if (theme === "auto") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return theme;
  }

  _watchForm() {
    const form = this.closest("form");
    if (form === null) {
      return;
    }
    const provider = this.getAttribute("provider") || "";
    const isInvisible = provider === "recaptcha-v3" || provider === "turnstile";
    if (!isInvisible) {
      return;
    }

    this._formSubmitHandler = async (event) => {
      if (this._verified) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();

      if (this._adapter === null || this._adapter === undefined) {
        return;
      }

      const timeout = new Promise((_, reject) => {
        setTimeout(() => reject(new Error("execute timeout")), 5000);
      });

      try {
        const token = await Promise.race([this._adapter.execute(), timeout]);
        this._onVerified(token);
        form.requestSubmit();
      } catch (err) {
        console.error("[mj-captcha] execute failed:", err);
        this.emit("mj-error", { code: "execute-failed", message: err.message });
      }
    };

    form.addEventListener("submit", this._formSubmitHandler, { capture: true });
    this.onTeardown(() => {
      form.removeEventListener("submit", this._formSubmitHandler, { capture: true });
    });
    return;
  }

  _unwatchForm() {
    return;
  }

  _onVerified(token) {
    this._token = token;
    this._verified = true;
    this._setFormValue(token);

    this._setStatus("verified", "Verification successful");
    this.emit("mj-verified", { token });

    const expirySeconds = parseInt(this.getAttribute("token-expiry") || "120", 10);
    if (expirySeconds > 0) {
      if (this._expiryTimer !== null) {
        clearTimeout(this._expiryTimer);
      }
      this._expiryTimer = setTimeout(() => {
        this._onExpired();
      }, expirySeconds * 1000);
    }
    return;
  }

  _onExpired() {
    this._token = "";
    this._verified = false;
    this._setFormValue("");
    this._setStatus("expired", "Verification expired, please try again");
    this.emit("mj-expired", {});
    return;
  }

  _setStatus(type, message) {
    this._statusEl.setAttribute("data-visible", "");
    this._statusEl.setAttribute("data-type", type);
    this._statusEl.textContent = message;
    return;
  }

  _showError(message) {
    this._containerEl.setAttribute("aria-busy", "false");
    this._statusEl.setAttribute("role", "alert");
    this._setStatus("error", message);
    return;
  }

  _showFallback(code) {
    this._containerEl.setAttribute("aria-busy", "false");
    this._fallbackEl.setAttribute("data-visible", "");
    this.emit("mj-error", { code, message: "Provider failed to load." });
    return;
  }

  _runValidation() {
    this._refreshValidity();
    const msg = this.validationMessage;
    const overrideMsg = this.getAttribute("error-message") || "";
    const displayMsg = overrideMsg.length > 0 ? overrideMsg : msg;

    if (displayMsg.length > 0) {
      this._errorEl.textContent = displayMsg;
      this._errorEl.setAttribute("data-visible", "");
      this._containerEl.setAttribute("aria-invalid", "true");
      this.emit("mj-invalid", { validationMessage: displayMsg });
    } else {
      this._errorEl.removeAttribute("data-visible");
      this._containerEl.setAttribute("aria-invalid", "false");
    }
    return;
  }

  _customValidity() {
    const required = this.hasAttribute("required");
    if (required && (this._token.length === 0 || !this._verified)) {
      return "Please complete the security verification.";
    }
    return "";
  }

  onFormReset(initial) {
    this._token = "";
    this._verified = false;
    this._setFormValue("");
    if (this._expiryTimer !== null) {
      clearTimeout(this._expiryTimer);
      this._expiryTimer = null;
    }
    if (this._adapter !== null && this._adapter !== undefined) {
      this._adapter.reset();
    }
    if (this._statusEl !== undefined) {
      this._statusEl.removeAttribute("data-visible");
    }
    if (this._errorEl !== undefined) {
      this._errorEl.removeAttribute("data-visible");
    }
    if (this._containerEl !== undefined) {
      this._containerEl.setAttribute("aria-invalid", "false");
    }
    this.emit("mj-reset", {});
    return;
  }

  get token() {
    return this._token;
  }

  get verified() {
    return this._verified;
  }

  get providerAdapter() {
    return this._providerAdapter;
  }

  set providerAdapter(adapter) {
    this._providerAdapter = adapter;
    if (this._containerEl !== undefined) {
      this._cleanupProvider();
      this._mountProvider();
    }
    return;
  }

  checkValidity() {
    this._refreshValidity();
    return this._internals !== null ? this._internals.checkValidity() : true;
  }

  reportValidity() {
    this._runValidation();
    return this._internals !== null ? this._internals.reportValidity() : true;
  }

  reset() {
    this.onFormReset("");
    return;
  }

  focus() {
    if (this._containerEl !== undefined) {
      const focusable = this._containerEl.querySelector("iframe, button, input, [tabindex]");
      if (focusable !== null) {
        focusable.focus();
      }
    }
    return;
  }
}
