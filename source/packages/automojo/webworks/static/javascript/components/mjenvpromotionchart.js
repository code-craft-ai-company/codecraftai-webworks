/*
 * mjenvpromotionchart.js
 *
 * <mj-env-promotion-chart> -- artifact promotion chart showing version and
 * health per environment with approval gates between promotions.
 *
 * SVG for the promotion arrow track; accessible summary list always present.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatDate } from "../core/intl.js";
import { announce } from "../core/announcer.js";

const ENV_COL_W = 180;
const ENV_COL_GAP = 48;
const GATE_SIZE = 28;

const HEALTH_CONFIG = {
  healthy:   { icon: "✓", label: "Healthy",   color: "var(--mj-color-success)"  },
  degraded:  { icon: "⚠", label: "Degraded",  color: "var(--mj-color-warning)"  },
  down:      { icon: "✗", label: "Down",       color: "var(--mj-color-danger)"   },
  unknown:   { icon: "?", label: "Unknown",    color: "var(--mj-text-muted)"     },
};

const GATE_STATUS_CONFIG = {
  pending:  { icon: "◎", color: "var(--mj-color-warning)" },
  approved: { icon: "✓", color: "var(--mj-color-success)" },
  rejected: { icon: "✗", color: "var(--mj-color-danger)"  },
  auto:     { icon: "→", color: "var(--mj-text-muted)"    },
};

const STYLES = `
:host {
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  background: var(--mj-bg);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  overflow: hidden;
}
.wrapper { display: flex; flex-direction: column; }
.header { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-bottom: 1px solid var(--mj-border); flex-wrap: wrap; }
.header strong { font-size: var(--mj-font-size-sm); }
.toggle-btn { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px var(--mj-space-2); cursor: pointer; color: var(--mj-text); }
.toggle-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.chart-area { overflow-x: auto; padding: var(--mj-space-3); }
.env-track { display: flex; align-items: center; gap: 0; min-height: 130px; }
.env-col { display: flex; flex-direction: column; align-items: center; min-width: ${ENV_COL_W}px; max-width: ${ENV_COL_W}px; background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-md); padding: var(--mj-space-3); cursor: pointer; transition: box-shadow var(--mj-motion-fast); }
.env-col:hover, .env-col:focus { box-shadow: var(--mj-elevation-2); outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.env-name { font-weight: var(--mj-font-weight-medium); font-size: var(--mj-font-size-sm); text-align: center; margin-bottom: var(--mj-space-2); }
.version-badge { font-family: var(--mj-font-mono); font-size: var(--mj-font-size-xs); background: var(--mj-bg-muted); border-radius: var(--mj-radius-pill); padding: 2px 8px; margin-bottom: var(--mj-space-2); text-align: center; }
.health-indicator { display: flex; align-items: center; gap: var(--mj-space-1); font-size: var(--mj-font-size-xs); }
.health-icon { font-size: 14px; }
.gate-col { display: flex; flex-direction: column; align-items: center; justify-content: center; min-width: ${ENV_COL_GAP}px; gap: var(--mj-space-2); }
.gate-diamond { width: ${GATE_SIZE}px; height: ${GATE_SIZE}px; transform: rotate(45deg); border: 2px solid var(--mj-color-warning); background: var(--mj-bg-muted); flex-shrink: 0; }
.gate-icon { position: absolute; font-size: 14px; }
.gate-btns { display: flex; gap: var(--mj-space-1); margin-top: 4px; }
.gate-approve { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-color-success-surface); color: var(--mj-color-success); border: 1px solid var(--mj-color-success); border-radius: var(--mj-radius-sm); padding: 2px 6px; cursor: pointer; }
.gate-reject { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-color-danger-surface); color: var(--mj-color-danger); border: 1px solid var(--mj-color-danger); border-radius: var(--mj-radius-sm); padding: 2px 6px; cursor: pointer; }
.gate-approve:focus-visible, .gate-reject:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.promo-arrow { font-size: 18px; color: var(--mj-border-strong); }
.detail-panel { padding: var(--mj-space-3); border-top: 1px solid var(--mj-border); background: var(--mj-bg-subtle); }
.detail-panel h3 { margin: 0 0 var(--mj-space-2); font-size: var(--mj-font-size-sm); }
.a11y-list-wrap { padding: var(--mj-space-3); }
.a11y-list-wrap ol { margin: 0; padding-left: var(--mj-space-5); font-size: var(--mj-font-size-sm); }
[hidden] { display: none !important; }
`;

export class MjEnvPromotionChart extends MjElement {
  static tagName = "mj-env-promotion-chart";
  static styles = STYLES;
  static watched = ["orientation", "density", "readonly", "live", "artifact-id"];

  constructor() {
    super();
    this._data = null;
    this._selectedEnvironment = null;
    this._selectedGate = null;
    this._showList = false;
    this._listId = nextId("mj-ep-list");
    this._pollTimer = null;
  }

  render() {
    return `
      <div class="wrapper" part="wrapper" role="img" aria-label="Environment promotion chart">
        <div class="header">
          <strong>Environment Promotion</strong>
          <span style="flex:1"></span>
          <button class="toggle-btn" aria-controls="${this._listId}" aria-expanded="false">Show summary list</button>
        </div>
        <div class="chart-area">
          <div class="env-track" part="env-track"></div>
        </div>
        <div class="detail-panel" part="environment-detail" hidden>
          <button class="close-detail" aria-label="Close">&#x2715;</button>
          <h3></h3>
          <div class="detail-content"></div>
          <slot name="environment-detail"></slot>
        </div>
        <div id="${this._listId}" class="a11y-list-wrap" hidden>
          <ol part="a11y-list"></ol>
        </div>
        <slot hidden></slot>
      </div>`;
  }

  afterRender() {
    this._track = this.$(".env-track");
    this._detailPanel = this.$(".detail-panel");
    this._detailContent = this.$(".detail-content");
    this._listWrap = this.$("#" + this._listId);
    this._listEl = this.$("ol");
    this._toggleBtn = this.$(".toggle-btn");
    this.listen(this._toggleBtn, "click", this._onToggleList.bind(this));
    this.listen(this.$(".close-detail"), "click", this._closeDetail.bind(this));
    if (this._data !== null) {
      this._draw();
    }
    return;
  }

  get data() {
    return this._data;
  }

  set data(value) {
    this._data = value;
    if (this._track !== undefined) {
      this._draw();
    }
    return;
  }

  get selectedEnvironment() {
    return this._selectedEnvironment;
  }

  get selectedGate() {
    return this._selectedGate;
  }

  get pendingGates() {
    const gates = (this._data && this._data.gates) || [];
    return gates.filter((g) => g.status === "pending");
  }

  _onToggleList() {
    this._showList = !this._showList;
    this._listWrap.hidden = !this._showList;
    this._toggleBtn.setAttribute("aria-expanded", String(this._showList));
    return;
  }

  _closeDetail() {
    this._detailPanel.hidden = true;
    this._selectedEnvironment = null;
    this.emit("mj-environment-deselect", {});
    return;
  }

  _draw() {
    const d = this._data;
    if (d === null || d === undefined) {
      return;
    }
    const environments = d.environments || [];
    const gates = d.gates || [];
    const promotions = d.promotions || [];
    const readonly = this.hasAttribute("readonly");

    if (this._track === null || this._track === undefined) {
      return;
    }

    const trackChildren = [];

    environments.forEach((env, ei) => {
      const health = env.health || "unknown";
      const hConfig = HEALTH_CONFIG[health] || HEALTH_CONFIG.unknown;
      const version = env.version || "—";
      const ariaLabel = `${env.name}, version: ${version}, health: ${hConfig.label}`;

      const colEl = document.createElement("div");
      colEl.className = "env-col";
      colEl.setAttribute("part", "environment-column");
      colEl.setAttribute("role", "button");
      colEl.setAttribute("tabindex", "0");
      colEl.setAttribute("aria-label", ariaLabel);
      colEl.setAttribute("data-env-id", env.id || env.name);

      colEl.innerHTML = `
        <div class="env-name" part="environment-header">${this._esc(env.name)}</div>
        <div class="version-badge" part="version-badge">${this._esc(version)}</div>
        <div class="health-indicator" part="health-indicator">
          <span class="health-icon" aria-hidden="true" style="color:${hConfig.color}">${hConfig.icon}</span>
          <span style="color:${hConfig.color}">${hConfig.label}</span>
        </div>
      `;

      this.listen(colEl, "click", (e) => { this._onEnvClick(e); });
      this.listen(colEl, "keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          this._onEnvClick(e);
        }
        return;
      });

      trackChildren.push(colEl);

      if (ei < environments.length - 1) {
        const gate = gates.find((g) => g.fromEnv === (env.id || env.name));
        const gateCol = document.createElement("div");
        gateCol.className = "gate-col";

        if (gate !== undefined) {
          const gConfig = GATE_STATUS_CONFIG[gate.status || "pending"] || GATE_STATUS_CONFIG.pending;
          const toEnvName = environments[ei + 1] && environments[ei + 1].name || "";
          gateCol.innerHTML = `
            <div style="position:relative;display:flex;align-items:center;justify-content:center;">
              <div class="gate-diamond" part="gate-node" style="border-color:${gConfig.color}" aria-hidden="true"></div>
              <span class="gate-icon" style="color:${gConfig.color}">${gConfig.icon}</span>
            </div>
          `;

          if (!readonly && gate.status === "pending") {
            const btnsWrap = document.createElement("div");
            btnsWrap.className = "gate-btns";
            btnsWrap.setAttribute("part", "gate-controls");
            btnsWrap.setAttribute("role", "group");
            btnsWrap.setAttribute("aria-label", `Approval gate between ${env.name} and ${toEnvName}, status: pending`);

            const approveBtn = document.createElement("button");
            approveBtn.className = "gate-approve";
            approveBtn.setAttribute("aria-label", `Approve promotion to ${toEnvName}`);
            approveBtn.textContent = "Approve";
            this.listen(approveBtn, "click", (e) => {
              e.stopPropagation();
              const proceed = this.emit("mj-gate-action", { gate, action: "approve", actor: "" }, { cancelable: true });
              if (proceed === false) {
                return;
              }
              gate.status = "approved";
              this._draw();
              return;
            });

            const rejectBtn = document.createElement("button");
            rejectBtn.className = "gate-reject";
            rejectBtn.setAttribute("aria-label", `Reject promotion to ${toEnvName}`);
            rejectBtn.textContent = "Reject";
            this.listen(rejectBtn, "click", (e) => {
              e.stopPropagation();
              const proceed = this.emit("mj-gate-action", { gate, action: "reject", actor: "" }, { cancelable: true });
              if (proceed === false) {
                return;
              }
              gate.status = "rejected";
              this._draw();
              return;
            });

            btnsWrap.appendChild(approveBtn);
            btnsWrap.appendChild(rejectBtn);
            gateCol.appendChild(btnsWrap);
          }
        } else {
          gateCol.innerHTML = `<span class="promo-arrow" aria-hidden="true">→</span>`;
        }

        trackChildren.push(gateCol);
      }
    });

    this._track.innerHTML = "";
    trackChildren.forEach((el) => {
      this._track.appendChild(el);
    });

    this._buildList(environments);

    const pending = this.pendingGates.length;
    const artifactId = this.getAttribute("artifact-id") || "";
    const wrapper = this.$(".wrapper");
    if (wrapper !== null) {
      wrapper.setAttribute("aria-label", `Environment promotion chart: ${artifactId || "artifact"}, ${environments.length} environments, ${pending} pending gates`);
    }
    this.emit("mj-data-load", { environments: environments.length, pendingGates: pending });
    return;
  }

  _buildList(environments) {
    if (this._listEl === null || this._listEl === undefined) {
      return;
    }
    const items = environments.map((env) => {
      const health = env.health || "unknown";
      const hConfig = HEALTH_CONFIG[health] || HEALTH_CONFIG.unknown;
      return `<li>${this._esc(env.name)}: version ${this._esc(env.version || "—")}, health: ${hConfig.label}</li>`;
    });
    this._listEl.innerHTML = items.join("");
    return;
  }

  _onEnvClick(event) {
    const col = event.currentTarget;
    const id = col.getAttribute("data-env-id");
    const environments = (this._data && this._data.environments) || [];
    const env = environments.find((e) => (e.id || e.name) === id);
    if (env !== undefined) {
      this._selectedEnvironment = env;
      const h3 = this._detailPanel.querySelector("h3");
      if (h3 !== null) {
        h3.textContent = env.name;
      }
      const health = env.health || "unknown";
      const hConfig = HEALTH_CONFIG[health] || HEALTH_CONFIG.unknown;
      this._detailContent.innerHTML = `<p><strong>Version:</strong> ${this._esc(env.version || "—")}</p><p><strong>Health:</strong> <span style="color:${hConfig.color}">${hConfig.icon} ${hConfig.label}</span></p>${env.lastPromotion ? `<p><strong>Last promoted:</strong> ${formatDate(new Date(env.lastPromotion))}</p>` : ""}`;
      this._detailPanel.hidden = false;
      this.emit("mj-environment-select", { environment: env });
    }
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._track !== undefined && this._data !== null) {
      this._draw();
    }
    return;
  }

  onDisconnected() {
    if (this._pollTimer !== null) {
      clearInterval(this._pollTimer);
      this._pollTimer = null;
    }
    return;
  }

  _esc(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
}
