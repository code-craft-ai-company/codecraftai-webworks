/*
 * chartpart.js
 *
 * ChartPart -- a mixin over MjElement shared by every chart part component
 * (plot, axis, grid, legend, title, tooltip, data-table). It handles
 * controller resolution, registration, and model delivery, so the part
 * components themselves stay thin and only implement `drawPart`.
 *
 *   export class MjChartPlot extends ChartPart(MjElement) { ... }
 *
 * A part component overrides:
 *   - drawPart(model, context)  -- render from the chart model + context;
 *   - onPartConnected()         -- optional extra connect-time setup.
 *
 * It inherits dock/anchor/context-menu/theming from MjElement.
 */

import { resolveController } from "./chartregistry.js";


export function ChartPart(Base) {
  class Part extends Base {
    constructor() {
      super()
      this._controller = null
      this._lastModel = null
      this._lastContext = null
    }

    onConnected() {
      this._controller = resolveController(this)

      if (this._controller !== null) {
        if (typeof this._controller.registerPart === "function") {
          this._controller.registerPart(this)
        }
        /* Pull the model immediately if the controller already has one. */
        const model = this._controller.chartModel
        if (model !== null && model !== undefined) {
          this.applyModel(model, this._controller.chartContext)
        }
      }

      this.onPartConnected()
      return
    }

    onDisconnected() {
      if (this._controller !== null &&
          typeof this._controller.unregisterPart === "function") {
        this._controller.unregisterPart(this)
      }
      this.onPartDisconnected()
      return
    }

    /*
     * Called by the controller (or on connect) with the current model and
     * the chart context (scales, dimensions, color scale). Caches them and
     * delegates to the component's `drawPart`.
     */
    applyModel(model, context) {
      this._lastModel = model
      this._lastContext = context !== undefined ? context : null
      if (this.shadowRoot !== null) {
        this.drawPart(model, this._lastContext)
      }
      return
    }

    /* The controller this part is bound to (may be null). */
    get controller() {
      return this._controller
    }

    /* ----- hooks for the concrete part component to override ----- */

    /*
     * Render the part from the chart model and context. Context carries
     * { scales, width, height, colorScale, orientation } once the
     * controller has computed layout; it may be null before then.
     */
    drawPart(model, context) {
      return
    }

    onPartConnected() {
      return
    }

    onPartDisconnected() {
      return
    }
  }

  return Part
}
