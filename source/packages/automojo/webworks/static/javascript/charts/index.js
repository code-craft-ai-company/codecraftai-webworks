/*
 * index.js
 *
 * Entry point for the automojo-webworks chart library. Importing this
 * module imports every renderer (each self-registers its chart type) and
 * registers the <mj-chart> controller and the coordinated part components.
 *
 *   <script type="module" src="/static/javascript/charts/index.js"></script>
 *
 * A chart is <mj-chart type="..."> fed JSON via the `data` property, `src`
 * URL, or an inline <script type="application/json">. The coordinated parts
 * <mj-chart-title>, <mj-chart-legend> and <mj-chart-data-table> bind to a
 * controller by its id and can be placed/docked independently.
 */

import { defineAll } from "../core/registry.js";

/* Renderers -- importing each file self-registers its chart type(s). */
import "./core/renderers/area.js";
import "./core/renderers/bar.js";
import "./core/renderers/beeswarm.js";
import "./core/renderers/boxplot.js";
import "./core/renderers/bullet.js";
import "./core/renderers/bump.js";
import "./core/renderers/calendarheatmap.js";
import "./core/renderers/cdf.js";
import "./core/renderers/chord.js";
import "./core/renderers/cohort.js";
import "./core/renderers/contour.js";
import "./core/renderers/control.js";
import "./core/renderers/curve.js";
import "./core/renderers/density.js";
import "./core/renderers/dothistogram.js";
import "./core/renderers/dotplot.js";
import "./core/renderers/errorbar.js";
import "./core/renderers/faceted.js";
import "./core/renderers/flowchart.js";
import "./core/renderers/flowmap.js";
import "./core/renderers/forest.js";
import "./core/renderers/freqresponse.js";
import "./core/renderers/funnel.js";
import "./core/renderers/funnelplot.js";
import "./core/renderers/gantt.js";
import "./core/renderers/gauge.js";
import "./core/renderers/geomap.js";
import "./core/renderers/glyph.js";
import "./core/renderers/heatmap.js";
import "./core/renderers/heatmaptable.js";
import "./core/renderers/hexbin.js";
import "./core/renderers/hierlayout.js";
import "./core/renderers/histogram.js";
import "./core/renderers/horizon.js";
import "./core/renderers/iconarray.js";
import "./core/renderers/journey.js";
import "./core/renderers/kanban.js";
import "./core/renderers/kpi.js";
import "./core/renderers/line.js";
import "./core/renderers/loglog.js";
import "./core/renderers/lollipop.js";
import "./core/renderers/marimekko.js";
import "./core/renderers/matrix.js";
import "./core/renderers/mosaic.js";
import "./core/renderers/network.js";
import "./core/renderers/ohlc.js";
import "./core/renderers/parallel.js";
import "./core/renderers/pareto.js";
import "./core/renderers/phase.js";
import "./core/renderers/pie.js";
import "./core/renderers/pixel.js";
import "./core/renderers/polar.js";
import "./core/renderers/qqplot.js";
import "./core/renderers/radar.js";
import "./core/renderers/resource.js";
import "./core/renderers/ridgeline.js";
import "./core/renderers/rug.js";
import "./core/renderers/sankey.js";
import "./core/renderers/scatter.js";
import "./core/renderers/scorecard.js";
import "./core/renderers/slope.js";
import "./core/renderers/smith.js";
import "./core/renderers/sparkline.js";
import "./core/renderers/spectrogram.js";
import "./core/renderers/spiral.js";
import "./core/renderers/splom.js";
import "./core/renderers/step.js";
import "./core/renderers/streamgraph.js";
import "./core/renderers/strip.js";
import "./core/renderers/survival.js";
import "./core/renderers/ternary.js";
import "./core/renderers/timeline.js";
import "./core/renderers/tornado.js";
import "./core/renderers/tree.js";
import "./core/renderers/upset.js";
import "./core/renderers/vectorfield.js";
import "./core/renderers/venn.js";
import "./core/renderers/violin.js";
import "./core/renderers/volume.js";
import "./core/renderers/voronoi.js";
import "./core/renderers/waffle.js";
import "./core/renderers/waterfall.js";
import "./core/renderers/wordcloud.js";

import { MjChart } from "./mjchart.js";
import { MjChartTitle } from "./mjcharttitle.js";
import { MjChartLegend } from "./mjchartlegend.js";
import { MjChartDataTable } from "./mjchartdatatable.js";

export const chartComponents = [
  MjChart, MjChartTitle, MjChartLegend, MjChartDataTable
];

/* Register the chart controller and parts (idempotent). */
export const registeredChartTags = defineAll(chartComponents);

export { rendererTypes, hasRenderer } from "./core/renderregistry.js";
