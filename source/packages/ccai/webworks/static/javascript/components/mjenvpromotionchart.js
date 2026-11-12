/*
 * mjenvpromotionchart.js
 *
 * <mj-env-promotion-chart> -- artifact promotion chart showing version and
 * health per environment with approval gates between promotions.
 *
 * Environment cards and gates are keyboard reachable (one tab stop, arrow
 * keys between them); a pending gate also offers Approve / Reject buttons
 * unless the chart is `readonly`. Every gate states its status in text. A
 * decision is shown in place, focus stays on the gate, the outcome is
 * announced, and the host's data object is not modified. A summary list of
 * environments and gates can be disclosed from the header.
 *
 * Live mode (`live`): every `poll-interval` ms (default 30000, at least
 * 5000) the chart refetches `src` when it has one, otherwise it emits
 * `mj-poll-tick` so the host can assign fresh data. A new version in an
 * environment emits `mj-promotion-update` and is announced.
 *
 * Data: `data` property, `src` attribute or inline JSON child --
 *   { environments: [{ id, name, version, health, lastPromotion }],
 *     gates: [{ fromEnv, status, name }],
 *     promotions: [{ environment, version, at }] }
 */

import { nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";
import { resolveChartData } from "../charts/core/jsonsource.js";
import {
  PM_CHART_STYLES, PmChartElement, DetailPanel, chartTime, detailPanelMarkup,
  emptyStateMarkup, findMark, formatChartDate, markSelection, replaceMarkup,
  setEmptyState, syncRovingMarks, toText, wireMarks
} from "./pmchartsupport.js";

const ENV_COL_W = 180;
const ENV_COL_GAP = 64;
const GATE_SIZE = 28;
const DEFAULT_POLL_MS = 30000;
const MIN_POLL_MS = 5000;

/* `labelKey` is the string key of the visible label, resolved with t() at use time. */
const HEALTH_CONFIG = {
  healthy:  { icon: "✓", labelKey: "mj.envPromotionChart.health.healthy",  color: "var(--mj-color-success)" },
  degraded: { icon: "⚠", labelKey: "mj.envPromotionChart.health.degraded", color: "var(--mj-color-warning)" },
  down:     { icon: "✗", labelKey: "mj.envPromotionChart.health.down",     color: "var(--mj-color-danger)" },
  unknown:  { icon: "?", labelKey: "mj.envPromotionChart.health.unknown",  color: "var(--mj-text-muted)" }
};

const GATE_STATUS_CONFIG = {
  pending:  { icon: "◎", labelKey: "mj.envPromotionChart.gateStatus.pending",  color: "var(--mj-color-warning)" },
  approved: { icon: "✓", labelKey: "mj.envPromotionChart.gateStatus.approved", color: "var(--mj-color-success)" },
  rejected: { icon: "✗", labelKey: "mj.envPromotionChart.gateStatus.rejected", color: "var(--mj-color-danger)" },
  auto:     { icon: "→", labelKey: "mj.envPromotionChart.gateStatus.auto",     color: "var(--mj-text-muted)" }
};

const STYLES = `
${PM_CHART_STYLES}
.live-badge { display: inline-flex; align-items: center; gap: 4px; font-size: var(--mj-font-size-xs); color: var(--mj-color-info); }
.live-dot { inline-size: 7px; block-size: 7px; border-radius: 50%; background: var(--mj-color-info); animation: mj-pulse 1.4s ease-in-out infinite; }
@keyframes mj-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
@media (prefers-reduced-motion: reduce) { .live-dot { animation: none; } }
.chart-area { overflow-x: auto; padding: var(--mj-space-3); }
.env-track { display: flex; align-items: stretch; gap: 0; min-block-size: 130px; }
:host([orientation="vertical"]) .env-track { flex-direction: column; align-items: center; }
.env-col { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: none; inline-size: ${ENV_COL_W}px; background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-md); padding: var(--mj-space-3); cursor: pointer; transition: box-shadow var(--mj-motion-fast); }
.env-col:hover { box-shadow: var(--mj-elevation-2); }
.env-col:focus { outline: none; }
.env-col:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.env-col[data-selected="true"] { border-color: var(--mj-accent); box-shadow: inset 0 0 0 1px var(--mj-accent); }
.env-name { font-weight: var(--mj-font-weight-medium); font-size: var(--mj-font-size-sm); text-align: center; margin-block-end: var(--mj-space-2); overflow-wrap: anywhere; }
.version-badge { font-family: var(--mj-font-mono); font-size: var(--mj-font-size-xs); background: var(--mj-bg-muted); border-radius: var(--mj-radius-pill); padding: 2px 8px; margin-block-end: var(--mj-space-2); text-align: center; max-inline-size: 100%; overflow-wrap: anywhere; }
.health-indicator { display: flex; align-items: center; gap: var(--mj-space-1); font-size: var(--mj-font-size-xs); }
.health-icon { font-size: 14px; }
.promoted-at { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); margin-block-start: var(--mj-space-1); text-align: center; }
.gate-col { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: none; min-inline-size: ${ENV_COL_GAP}px; padding: var(--mj-space-2) var(--mj-space-1); gap: var(--mj-space-1); }
.gate-mark { display: flex; flex-direction: column; align-items: center; gap: var(--mj-space-1); background: none; border: none; border-radius: var(--mj-radius-sm); padding: var(--mj-space-1); cursor: pointer; color: inherit; font: inherit; }
.gate-mark:focus { outline: none; }
.gate-mark:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.gate-mark[data-selected="true"] .gate-diamond { box-shadow: 0 0 0 2px var(--mj-accent); }
.gate-shape { position: relative; display: flex; align-items: center; justify-content: center; inline-size: ${GATE_SIZE + 8}px; block-size: ${GATE_SIZE + 8}px; }
.gate-diamond { position: absolute; inline-size: ${GATE_SIZE}px; block-size: ${GATE_SIZE}px; transform: rotate(45deg); border: 2px solid var(--mj-color-warning); background: var(--mj-bg-muted); }
.gate-icon { position: relative; font-size: 14px; }
.gate-status { font-size: 10px; text-align: center; max-inline-size: ${ENV_COL_GAP + 24}px; }
.gate-btns { display: flex; gap: var(--mj-space-1); }
.gate-approve, .gate-reject { font: inherit; font-size: var(--mj-font-size-xs); border-radius: var(--mj-radius-sm); padding: 2px 6px; min-block-size: 24px; cursor: pointer; }
.gate-approve { background: var(--mj-color-success-surface); color: var(--mj-color-success); border: 1px solid var(--mj-color-success); }
.gate-reject { background: var(--mj-color-danger-surface); color: var(--mj-color-danger); border: 1px solid var(--mj-color-danger); }
.gate-approve:focus-visible, .gate-reject:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.promo-arrow { font-size: 18px; color: var(--mj-text-muted); }
:host([orientation="vertical"]) .promo-arrow { transform: rotate(90deg); }
`;

export class MjEnvPromotionChart extends PmChartElement {
  static tagName = "mj-env-promotion-chart";
  static styles = STYLES;
  static watched = ["orientation", "density", "readonly", "live", "poll-interval", "artifact-id"];

  constructor() {
    super()
    this._selectedEnvironment = null
    this._selectedGate = null
    this._selectedKey = null

    /* Gate statuses decided in this chart, by gate index. */
    this._gateDecisions = new Map()

    /* Versions of the previous data, by environment id, for live updates. */
    this._previousVersions = new Map()

    this._pollTimer = null
    this._listId = nextId("mj-ep-list")
    this._detailId = nextId("mj-ep-detail")
  }

  render() {
    const markup = html`
      <div class="wrapper" part="wrapper" role="region" aria-label="${t("mj.envPromotionChart.label")}">
        <div class="toolbar header">
          <strong class="toolbar-title">${t("mj.envPromotionChart.title")}</strong>
          <span class="artifact-label"></span>
          <span class="live-badge" part="live-indicator" hidden><span class="live-dot" aria-hidden="true"></span> ${t("mj.envPromotionChart.live")}</span>
          <span class="toolbar-spacer"></span>
          <button class="chart-button toggle-btn" type="button" aria-controls="${this._listId}" aria-expanded="false">${t("mj.envPromotionChart.showSummaryList")}</button>
        </div>
        <div class="chart-area">
          <div class="env-track" part="env-track" role="group" aria-label="${t("mj.envPromotionChart.environments")}"></div>
          ${emptyStateMarkup()}
        </div>
        ${detailPanelMarkup({ headingId: this._detailId, part: "environment-detail", slotName: "environment-detail", placement: "inline" })}
        <div id="${this._listId}" class="a11y-list-wrap" hidden>
          <ol part="a11y-list"></ol>
        </div>
      </div>`
    return markup
  }

  afterRender() {
    this._track = this.$(".env-track")
    this._wrapper = this.$(".wrapper")
    this._listEl = this.$("ol")
    this._liveBadge = this.$(".live-badge")

    this._detail = new DetailPanel(this, this.$(".detail-panel"), () => {
      this._onDetailClosed()
    })

    wireMarks(this, this._track, (mark) => {
      this._onMarkActivate(mark)
    }, (key) => {
      this._activeMarkKey = key
    })

    /* Approve / Reject buttons are rebuilt with the track; one listener serves all. */
    this.listen(this._track, "click", (event) => {
      const button = event.target.closest("[data-gate-action]")
      if (button !== null) {
        event.stopPropagation()
        this._onGateAction(Number(button.getAttribute("data-gate-index")), button.getAttribute("data-gate-action"))
      }
    })

    this.setupChart({
      alternativeButton: this.$(".toggle-btn"),
      alternativeRegion: this.$(`#${this._listId}`)
    })
    this._syncLive()
    return
  }

  onDisconnected() {
    this._stopPolling()
    return
  }

  get selectedEnvironment() {
    return this._selectedEnvironment
  }

  get selectedGate() {
    return this._selectedGate
  }

  get pendingGates() {
    const pending = this._gates().filter((gate) => gate.status === "pending").map((gate) => gate.source)
    return pending
  }

  onDataChanged() {
    this._selectedEnvironment = null
    this._selectedGate = null
    this._selectedKey = null
    this._gateDecisions = new Map()
    if (this._detail !== undefined) {
      this._detail.close(false)
    }
    return
  }

  onDataDrawn() {
    const environments = this._environments()

    if (this.flag("live") === true) {
      environments.forEach((environment) => {
        const previous = this._previousVersions.get(environment.id)
        if (previous !== undefined && previous !== environment.version) {
          this.emit("mj-promotion-update", { environment: environment.source, version: environment.version })
          announce(t("mj.envPromotionChart.versionChanged", { name: environment.name, version: environment.version }), "polite")
        }
      })
    }
    this._previousVersions = new Map()
    environments.forEach((environment) => {
      this._previousVersions.set(environment.id, environment.version)
    })

    const pending = this.pendingGates.length
    this.emit("mj-data-load", { environments: environments.length, pendingGates: pending })
    if (this.flag("live") === true && pending > 0) {
      announce(t("mj.envPromotionChart.pendingAnnouncement", { count: pending }), "polite")
    }
    return
  }

  onChartAttributeChanged(name, oldValue, newValue) {
    if (name === "live" || name === "poll-interval") {
      this._syncLive()
      return
    }
    if (name === "readonly" && this.flag("readonly") === true && this._detail !== undefined) {
      this._detail.close(false)
    }
    this.drawChart()
    return
  }

  /* ----- live mode ----- */

  _pollInterval() {
    const parsed = parseInt(this.getAttribute("poll-interval"), 10)
    const interval = Number.isFinite(parsed) === true ? Math.max(MIN_POLL_MS, parsed) : DEFAULT_POLL_MS
    return interval
  }

  _syncLive() {
    this._stopPolling()
    const live = this.flag("live")
    if (this._liveBadge !== undefined) {
      this._liveBadge.hidden = live === false
    }
    if (live === true && this.isConnected === true) {
      this._pollTimer = window.setInterval(() => {
        this._poll()
      }, this._pollInterval())
    }
    return
  }

  _stopPolling() {
    if (this._pollTimer !== null) {
      window.clearInterval(this._pollTimer)
      this._pollTimer = null
    }
    return
  }

  _poll() {
    const src = this.getAttribute("src")
    if (src !== null && src.trim().length > 0) {
      resolveChartData(this, null).then((loaded) => {
        if (loaded !== null && loaded !== undefined) {
          this.data = loaded
        }
      }).catch((error) => {
        const message = error !== null && error !== undefined && error.message !== undefined ? error.message : t("mj.envPromotionChart.loadError")
        this.emit("mj-error", { message: message })
      })
    } else {
      this.emit("mj-poll-tick", {})
    }
    return
  }

  /* ----- data ----- */

  _environments() {
    const source = this._data !== null && Array.isArray(this._data.environments) === true ? this._data.environments : []
    const promotions = this._data !== null && Array.isArray(this._data.promotions) === true ? this._data.promotions : []

    const environments = source.map((environment, index) => {
      const safe = environment !== null && typeof environment === "object" ? environment : {}
      const hasId = safe.id !== undefined && safe.id !== null
      const hasName = safe.name !== undefined && safe.name !== null && toText(safe.name).length > 0
      const id = hasId === true ? safe.id : (hasName === true ? safe.name : `env-${index + 1}`)
      const health = HEALTH_CONFIG[safe.health] !== undefined ? safe.health : "unknown"

      /* Last promotion: the field on the environment, else the newest promotion record. */
      let lastPromotion = safe.lastPromotion
      let latestTime = chartTime(lastPromotion)
      promotions.forEach((promotion) => {
        const record = promotion !== null && typeof promotion === "object" ? promotion : {}
        const target = record.environment !== undefined ? record.environment : record.toEnv
        const time = chartTime(record.at)
        if (target === id && Number.isNaN(time) === false && (Number.isNaN(latestTime) === true || time > latestTime)) {
          latestTime = time
          lastPromotion = record.at
        }
      })

      const described = {
        source: environment,
        index: index,
        id: id,
        name: hasName === true ? toText(safe.name) : toText(id),
        version: safe.version !== undefined && safe.version !== null && toText(safe.version).length > 0 ? toText(safe.version) : "—",
        health: health,
        lastPromotion: Number.isNaN(latestTime) === false ? lastPromotion : null
      }
      return described
    })
    return environments
  }

  _gates() {
    const source = this._data !== null && Array.isArray(this._data.gates) === true ? this._data.gates : []
    const gates = source.map((gate, index) => {
      const safe = gate !== null && typeof gate === "object" ? gate : {}
      const declared = GATE_STATUS_CONFIG[safe.status] !== undefined ? safe.status : "pending"
      const described = {
        source: gate,
        index: index,
        fromEnv: safe.fromEnv,
        name: safe.name !== undefined && safe.name !== null ? toText(safe.name) : "",
        status: this._gateDecisions.has(index) === true ? this._gateDecisions.get(index) : declared
      }
      return described
    })
    return gates
  }

  drawChart() {
    const environments = this._environments()
    const gates = this._gates()
    const readonly = this.flag("readonly")
    const compact = this.getAttribute("density") === "compact"
    const artifactId = this.getAttribute("artifact-id") || ""

    this.$(".artifact-label").textContent = artifactId.length > 0 ? `· ${artifactId}` : ""
    this._buildList(environments, gates)

    if (environments.length === 0) {
      replaceMarkup(this._track, "")
      this._track.hidden = true
      setEmptyState(this, "empty")
      this._wrapper.setAttribute("aria-label", t("mj.envPromotionChart.noEnvironments"))
      return
    }

    this._track.hidden = false
    setEmptyState(this, "ready")

    const parts = []
    environments.forEach((environment, position) => {
      const health = HEALTH_CONFIG[environment.health]
      const healthText = t(health.labelKey)
      const promotedText = environment.lastPromotion !== null ? formatChartDate(environment.lastPromotion, { dateStyle: "medium" }) : ""
      const label = promotedText.length > 0
        ? t("mj.envPromotionChart.environmentLabelPromoted", { name: environment.name, version: environment.version, health: healthText, date: promotedText })
        : t("mj.envPromotionChart.environmentLabel", { name: environment.name, version: environment.version, health: healthText })

      parts.push(html`<div class="env-col" part="environment-column" role="button" tabindex="-1" aria-label="${label}" data-mark="env:${environment.index}">
        <div class="env-name" part="environment-header">${environment.name}</div>
        <div class="version-badge" part="version-badge">${environment.version}</div>
        <div class="health-indicator" part="health-indicator">
          <span class="health-icon" aria-hidden="true" style="color:${health.color}">${health.icon}</span>
          <span class="${compact === true ? "mj-visually-hidden" : ""}" style="color:${health.color}">${healthText}</span>
        </div>
        ${compact === false && promotedText.length > 0 ? html`<div class="promoted-at" part="promoted-at">${t("mj.envPromotionChart.promoted", { date: promotedText })}</div>` : html``}
      </div>`)

      if (position < environments.length - 1) {
        const next = environments[position + 1]
        const gate = gates.find((candidate) => candidate.fromEnv === environment.id)
        if (gate !== undefined) {
          const config = GATE_STATUS_CONFIG[gate.status]
          const statusText = t(config.labelKey)
          const gateTitle = this._gateTitle(gate)
          const gateLabel = t("mj.envPromotionChart.gateLabel", { gate: gateTitle, from: environment.name, to: next.name, status: statusText })
          const decide = readonly === false && gate.status === "pending"
          const buttons = decide === true ? html`<div class="gate-btns" part="gate-controls" role="group" aria-label="${t("mj.envPromotionChart.decidePromotion", { name: next.name })}"><button class="gate-approve" type="button" data-gate-action="approve" data-gate-index="${gate.index}" aria-label="${t("mj.envPromotionChart.approvePromotion", { name: next.name })}">${t("mj.envPromotionChart.approve")}</button><button class="gate-reject" type="button" data-gate-action="reject" data-gate-index="${gate.index}" aria-label="${t("mj.envPromotionChart.rejectPromotion", { name: next.name })}">${t("mj.envPromotionChart.reject")}</button></div>` : html``
          parts.push(html`<div class="gate-col"><div class="gate-mark" role="button" tabindex="-1" aria-label="${gateLabel}" data-mark="gate:${gate.index}"><span class="gate-shape" aria-hidden="true"><span class="gate-diamond" part="gate-node" style="border-color:${config.color}"></span><span class="gate-icon" style="color:${config.color}">${config.icon}</span></span><span class="gate-status" part="gate-status" style="color:${config.color}" aria-hidden="true">${statusText}</span></div>${buttons}</div>`)
        } else {
          parts.push(html`<div class="gate-col"><span class="promo-arrow" aria-hidden="true">→</span><span class="mj-visually-hidden">${t("mj.envPromotionChart.then")}</span></div>`)
        }
      }
    })

    replaceMarkup(this._track, html`${parts}`)
    this._activeMarkKey = syncRovingMarks(this._track, this._activeMarkKey)
    markSelection(this._track, this._selectedKey)

    const pending = gates.filter((gate) => gate.status === "pending").length
    const summary = t("mj.envPromotionChart.summary", {
      artifact: artifactId.length > 0 ? artifactId : t("mj.envPromotionChart.artifactFallback"),
      environments: t("mj.envPromotionChart.environmentCount", { count: environments.length }),
      pendingGates: t("mj.envPromotionChart.pendingGateCount", { count: pending })
    })
    this._wrapper.setAttribute("aria-label", summary)
    return
  }

  _buildList(environments, gates) {
    const items = []
    environments.forEach((environment, position) => {
      const health = HEALTH_CONFIG[environment.health]
      const text = environment.lastPromotion !== null
        ? t("mj.envPromotionChart.listEnvironmentPromoted", { name: environment.name, version: environment.version, health: t(health.labelKey), date: formatChartDate(environment.lastPromotion, { dateStyle: "medium" }) })
        : t("mj.envPromotionChart.listEnvironment", { name: environment.name, version: environment.version, health: t(health.labelKey) })
      items.push(html`<li>${text}</li>`)

      const gate = gates.find((candidate) => candidate.fromEnv === environment.id)
      const next = environments[position + 1]
      if (gate !== undefined && next !== undefined) {
        items.push(html`<li>${t("mj.envPromotionChart.listGate", { gate: this._gateTitle(gate), from: environment.name, to: next.name, status: t(GATE_STATUS_CONFIG[gate.status].labelKey) })}</li>`)
      }
    })
    this._listEl.innerHTML = String(html`${items}`)
    return
  }

  /* "<name> gate", or the generic title for an unnamed gate. */
  _gateTitle(gate) {
    const title = gate.name.length > 0 ? t("mj.envPromotionChart.gateNamed", { name: gate.name }) : t("mj.envPromotionChart.gateDefault")
    return title
  }

  _onMarkActivate(mark) {
    const key = mark.getAttribute("data-mark")
    const separator = key.indexOf(":")
    const kind = key.slice(0, separator)
    const index = Number(key.slice(separator + 1))
    const findOpener = () => {
      const opener = findMark(this._track, key)
      return opener
    }

    if (kind === "env") {
      const environment = this._environments()[index]
      if (environment !== undefined) {
        const health = HEALTH_CONFIG[environment.health]
        this._selectedEnvironment = environment.source
        this._selectedGate = null
        this._selectedKey = key
        markSelection(this._track, key)
        const content = html`<p><strong>${t("mj.envPromotionChart.versionField")}</strong> ${environment.version}</p><p><strong>${t("mj.envPromotionChart.healthField")}</strong> <span style="color:${health.color}">${health.icon} ${t(health.labelKey)}</span></p>${environment.lastPromotion !== null ? html`<p><strong>${t("mj.envPromotionChart.lastPromotedField")}</strong> ${formatChartDate(environment.lastPromotion, { dateStyle: "medium", timeStyle: "short" })}</p>` : html``}`
        this._detail.open(environment.name, content, findOpener)
        this.emit("mj-environment-select", { environment: environment.source })
      }
    } else if (kind === "gate") {
      const gate = this._gates()[index]
      if (gate !== undefined) {
        const environments = this._environments()
        const fromPosition = environments.findIndex((environment) => environment.id === gate.fromEnv)
        const from = environments[fromPosition]
        const to = environments[fromPosition + 1]
        this._selectedGate = gate.source
        this._selectedEnvironment = null
        this._selectedKey = key
        markSelection(this._track, key)
        const content = html`<p><strong>${t("mj.envPromotionChart.statusField")}</strong> ${t(GATE_STATUS_CONFIG[gate.status].labelKey)}</p>${from !== undefined && to !== undefined ? html`<p><strong>${t("mj.envPromotionChart.promotionField")}</strong> ${t("mj.envPromotionChart.promotionRoute", { from: from.name, to: to.name })}</p>` : html``}`
        this._detail.open(this._gateTitle(gate), content, findOpener)
        this.emit("mj-gate-select", { gate: gate.source })
      }
    }
    return
  }

  _onDetailClosed() {
    const hadEnvironment = this._selectedEnvironment !== null
    const hadGate = this._selectedGate !== null
    this._selectedEnvironment = null
    this._selectedGate = null
    this._selectedKey = null
    markSelection(this._track, null)
    if (hadEnvironment === true) {
      this.emit("mj-environment-deselect", {})
    } else if (hadGate === true) {
      this.emit("mj-gate-deselect", {})
    }
    return
  }

  /*
   * Approve or reject a pending gate. `mj-gate-action` is cancelable: the
   * host cancels it to handle the decision itself (and assigns new data
   * later). Otherwise the decision is shown here -- the host's data object
   * is not modified -- `mj-gate-change` reports it, focus moves to the gate
   * and the outcome is announced.
   */
  _onGateAction(index, action) {
    const gate = this._gates()[index]
    if (gate === undefined || gate.status !== "pending" || this.flag("readonly") === true) {
      return
    }

    const actor = this.getAttribute("actor") || ""
    const proceed = this.emit("mj-gate-action", { gate: gate.source, action: action, actor: actor }, { cancelable: true })
    if (proceed === false) {
      return
    }

    const status = action === "approve" ? "approved" : "rejected"
    const key = `gate:${index}`
    this._gateDecisions.set(index, status)
    this._activeMarkKey = key
    this.drawChart()

    const mark = findMark(this._track, key)
    if (mark !== null) {
      mark.focus()
    }
    this.emit("mj-gate-change", { gate: gate.source, status: status, actor: actor })
    const fallback = status === "approved" ? t("mj.envPromotionChart.gateApproved") : t("mj.envPromotionChart.gateRejected")
    announce(mark !== null ? mark.getAttribute("aria-label") : fallback, "polite")
    return
  }
}
