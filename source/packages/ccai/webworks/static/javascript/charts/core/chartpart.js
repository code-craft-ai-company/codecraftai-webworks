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
 * A part that overrides onAttributeChanged calls
 * super.onAttributeChanged(name, oldValue, newValue) so a change of the
 * `chart` attribute re-binds it.
 *
 * It inherits dock/anchor/context-menu/theming from MjElement.
 */

import { resolveController, CONTROLLER_CONNECT_EVENT } from "./chartregistry.js";


export function ChartPart(Base) {
  class Part extends Base {
    constructor() {
      super()
      this._controller = null
      this._lastModel = null
      this._lastContext = null
    }

    onConnected() {
      this._bindController()

      /*
       * The controller may enter the document (or be given its id) after
       * this part: it announces itself and the part resolves again.
       */
      this.listen(document, CONTROLLER_CONNECT_EVENT, () => {
        this._bindController()
      })

      this.onPartConnected()
      return
    }

    onDisconnected() {
      this._releaseController()
      this.onPartDisconnected()
      return
    }

    onAttributeChanged(name, oldValue, newValue) {
      /* Before the first render onConnected does the binding. */
      if (name === "chart" && this._rendered === true && this.isConnected === true) {
        this._bindController()
      }
      return
    }

    /*
     * Resolve the controller this part belongs to and register with it.
     * Runs on connect, when the `chart` attribute changes, and whenever a
     * controller announces itself. Registering delivers the controller's
     * current model, so the model is not pulled a second time here.
     */
    _bindController() {
      let found = resolveController(this)

      /*
       * An <mj-chart> that has not been upgraded yet cannot take a part.
       * It announces itself when it connects, and the part binds then.
       */
      if (found !== null && typeof found.registerPart !== "function") {
        found = null
      }
      if (found === this._controller) {
        return
      }

      this._releaseController()
      this._controller = found

      if (found !== null) {
        found.registerPart(this)
      } else {
        /* No controller (any more): drop what the old one supplied. */
        this.applyModel(null, null)
      }
      return
    }

    _releaseController() {
      if (this._controller !== null &&
          typeof this._controller.unregisterPart === "function") {
        this._controller.unregisterPart(this)
      }
      this._controller = null
      return
    }

    /*
     * Called by the controller with the current model and the chart
     * context. Caches them and delegates to the component's `drawPart`.
     * The model is null when the chart has no data or failed to load.
     */
    applyModel(model, context) {
      this._lastModel = model !== undefined ? model : null
      this._lastContext = context !== undefined ? context : null
      if (this._rendered === true) {
        this.drawPart(this._lastModel, this._lastContext)
      }
      return
    }

    /* The controller this part is bound to (may be null). */
    get controller() {
      return this._controller
    }

    /* ----- hooks for the concrete part component to override ----- */

    /*
     * Render the part from the chart model and context. The context is
     * the object described at MjChart.chartContext: { type, width, height,
     * orientation, label, colorScale, colorFor, hiddenSeries, legend,
     * table }. Both arguments are null while the chart has nothing to show.
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
