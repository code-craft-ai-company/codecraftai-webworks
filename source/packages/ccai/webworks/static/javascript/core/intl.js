/*
 * intl.js
 *
 * Localization and locale-aware formatting hook. Components read user-facing
 * default strings through `t()` and format numbers/dates/currency through the
 * helpers here, all built on the platform Intl APIs. Consumers can override
 * the locale and string table without rebuilding components.
 */

let currentLocale = (typeof navigator !== "undefined" && navigator.language) || "en";

/*
 * The default (English) string table. Every key a component passes to `t()`
 * must be registered here: `t()` returns the key itself on a miss, so an
 * unregistered key renders as raw text such as "mj.pagination.next" and the
 * `t(key) || "fallback"` pattern some components use never reaches its
 * fallback. `{name}` tokens are filled from the `params` argument of `t()`.
 *
 * A plural entry is an object keyed by Intl.PluralRules categories ("zero",
 * "one", "two", "few", "many", "other"); `t()` picks the form for
 * `params.count` in the current locale and falls back to "other".
 */
const STRINGS = {
  "core.clear": "Clear",
  "core.close": "Close",
  "core.loading": "Loading",
  "core.noResults": "No results",
  "core.required": "This field is required.",
  "core.selectAll": "Select all",
  "core.previous": "Previous",
  "core.next": "Next",
  "core.expand": "Expand",
  "core.collapse": "Collapse",
  "core.remove": "Remove",
  "core.search": "Search",

  "mj.appBar.navLabel": "Main",
  "mj.appBar.openNav": "Open navigation",
  "mj.appBar.closeNav": "Close navigation",
  "mj.appShell.navLabel": "Primary navigation",
  "mj.appShell.inspectorLabel": "Inspector",
  "mj.breadcrumb.navLabel": "Breadcrumb",
  "mj.breadcrumb.expand": "Show {count} hidden breadcrumbs",
  "mj.link.externalLabel": "opens in a new tab",
  "mj.pagination.navLabel": "Pagination",
  "mj.pagination.previous": "Previous",
  "mj.pagination.next": "Next",
  "mj.pagination.pageLabel": "Page {page}",
  "mj.pagination.currentPageLabel": "Page {page}, current",
  "mj.pagination.pageOf": "Page {page} of {total}",
  "mj.pagination.summary": "Showing {from}–{to} of {total}",
  "mj.select.noOptions": "No options",
  "mj.sideNav.navLabel": "Navigation",
  "mj.sideNav.collapse": "Collapse navigation",
  "mj.skipLink.label": "Skip to main content",
  "mj.toc.navLabel": "On this page",
  "mj.toc.empty": "No sections found",
  "mj.treeNav.navLabel": "Navigation",
  "mj.wizard.label": "Wizard",
  "mj.wizard.next": "Next",
  "mj.wizard.back": "Back",
  "mj.wizard.submit": "Submit",

  /* mj-alert */
  "mj.alert.info": "Info",
  "mj.alert.success": "Success",
  "mj.alert.warning": "Warning",
  "mj.alert.error": "Error",

  /* mj-avatar */
  "mj.avatar.presence.online": "Online",
  "mj.avatar.presence.away": "Away",
  "mj.avatar.presence.busy": "Busy",
  "mj.avatar.presence.offline": "Offline",
  "mj.avatar.unknownUser": "Unknown user",

  /* mj-badge */
  "mj.badge.online": "Online",
  "mj.badge.away": "Away",
  "mj.badge.busy": "Busy",
  "mj.badge.offline": "Offline",
  "mj.badge.dnd": "Do not disturb",
  "mj.badge.overflow": "{max}+",

  /* mj-button */
  "mj.button.done": "Done",

  /* mj-chip */
  "mj.chip.removeItem": "Remove {label}",

  /* mj-copy-button */
  "mj.copyButton.copy": "Copy",
  "mj.copyButton.copied": "Copied!",
  "mj.copyButton.failed": "Copy failed",

  /* mj-diagram */
  "mj.diagram.canvasLabel": "Diagram canvas",
  "mj.diagram.zoomIn": "Zoom in",
  "mj.diagram.zoomOut": "Zoom out",
  "mj.diagram.fitToView": "Fit to view",
  "mj.diagram.fit": "Fit",
  "mj.diagram.nodeList": "Diagram nodes",
  "mj.diagram.nodeDetails": "Node details",
  "mj.diagram.loading": "Loading diagram…",
  "mj.diagram.empty": "No nodes to display.",
  "mj.diagram.zoomLevel": "Zoom: {percent}%",

  /* mj-favorite-button */
  "mj.favoriteButton.favorite": "Favorite",
  "mj.favoriteButton.unfavorite": "Unfavorite",
  "mj.favoriteButton.like": "Like",
  "mj.favoriteButton.unlike": "Unlike",
  "mj.favoriteButton.bookmark": "Bookmark",
  "mj.favoriteButton.removeBookmark": "Remove bookmark",

  /* mj-gauge */
  "mj.gauge.label": "Gauge",

  /* mj-image */
  "mj.image.loadError": "Image failed to load",

  /* mj-map */
  "mj.map.label": "Map",
  "mj.map.zoomIn": "Zoom in",
  "mj.map.zoomOut": "Zoom out",
  "mj.map.closePopup": "Close popup",
  "mj.map.loading": "Loading map…",
  "mj.map.zoomedTo": "Zoomed to level {zoom}",
  "mj.map.noAdapter": "No map adapter configured. Set the adapter property.",

  /* mj-media-player */
  "mj.mediaPlayer.label": "Media player",
  "mj.mediaPlayer.mediaControls": "Media controls",
  "mj.mediaPlayer.play": "Play",
  "mj.mediaPlayer.pause": "Pause",
  "mj.mediaPlayer.replay": "Replay",
  "mj.mediaPlayer.seek": "Seek",
  "mj.mediaPlayer.seekValue": "{current} of {duration}",
  "mj.mediaPlayer.mute": "Mute",
  "mj.mediaPlayer.unmute": "Unmute",
  "mj.mediaPlayer.volume": "Volume",
  "mj.mediaPlayer.playbackSpeed": "Playback speed",
  "mj.mediaPlayer.speedOption": "{rate}x",
  "mj.mediaPlayer.captions": "Captions",
  "mj.mediaPlayer.captionsShort": "CC",
  "mj.mediaPlayer.fullscreen": "Fullscreen",
  "mj.mediaPlayer.exitFullscreen": "Exit fullscreen",
  "mj.mediaPlayer.transcript": "Transcript",
  "mj.mediaPlayer.noTranscript": "No transcript available",
  "mj.mediaPlayer.live": "Live",
  "mj.mediaPlayer.buffering": "Buffering…",
  "mj.mediaPlayer.mediaError": "Media error (code {code})",

  /* mj-share-button */
  "mj.shareButton.share": "Share",
  "mj.shareButton.shareVia": "Share via",
  "mj.shareButton.copyLink": "Copy link",
  "mj.shareButton.email": "Email",
  "mj.shareButton.linkCopied": "Link copied",
  "mj.shareButton.copyFailed": "Copy failed",

  /* mj-sparkline */
  "mj.sparkline.pointLabel": "{index}: {value}",

  /* mj-upload-button */
  "mj.uploadButton.selected": { one: "{count} file selected", other: "{count} files selected" },
  "mj.uploadButton.fileCount": { one: "{count} file", other: "{count} files" },

  /* mj-chart, mj-chart-data-table (charts/**; routed through t() by the charts owner) */
  "mj.chart.empty": "No chart data supplied.",
  "mj.chart.loadFailed": "Chart data could not be loaded.",
  "mj.chart.invalidData": "Chart data is not valid.",
  "mj.chart.noRenderer": "No renderer for chart type \"{type}\".",
  "mj.chart.renderError": "Chart render error: {message}",
  "mj.chart.tableCaption": "Chart data",
  "mj.chart.tableTruncated": { one: "Only the first {count} row is shown.", other: "Only the first {count} rows are shown." },
  "mj.chart.tableAllSeriesHidden": "All series are hidden.",
  "mj.chart.figureLabel": "{type} chart",

  /* mj-bulk-action-bar */
  "mj.bulkActionBar.toolbarLabel": "Bulk actions",
  "mj.bulkActionBar.actionsLabel": "Actions for selected rows",
  "mj.bulkActionBar.clearSelection": "Clear selection",
  "mj.bulkActionBar.selected": { one: "{countText} selected", other: "{countText} selected" },

  /* mj-column-picker */
  "mj.columnPicker.label": "Columns",
  "mj.columnPicker.panelLabel": "{label} picker",
  "mj.columnPicker.reset": "Reset",
  "mj.columnPicker.apply": "Apply",
  "mj.columnPicker.lockedDescription": "Locked column: always shown, cannot be moved.",
  "mj.columnPicker.reorderColumn": "Reorder {label}",
  "mj.columnPicker.minVisible": { one: "At least one column must remain visible.", other: "At least {count} columns must remain visible." },
  "mj.columnPicker.columnShown": "Column {label} shown.",
  "mj.columnPicker.columnHidden": "Column {label} hidden.",
  "mj.columnPicker.movedToPositionOf": "{label} moved to position {position} of {total}.",
  "mj.columnPicker.movedToPosition": "{label} moved to position {position}.",
  "mj.columnPicker.reorderCanceled": "Reorder canceled.",
  "mj.columnPicker.grabbed": "Grabbed. Use the arrow keys to move, Enter to drop, Escape to cancel.",
  "mj.columnPicker.columnsReset": "Columns reset.",

  /* mj-kanban */
  "mj.kanban.label": "Kanban board",
  "mj.kanban.loading": "Loading…",
  "mj.kanban.loadFailed": "Failed to load the board.",
  "mj.kanban.columnLabel": { one: "{label} ({count} card)", other: "{label} ({count} cards)" },
  "mj.kanban.wipLimit": "{count} of {limit} WIP limit",
  "mj.kanban.wipLimitExceeded": "{count} of {limit} WIP limit — exceeded",
  "mj.kanban.wipLimitAtLimit": "{count} of {limit} WIP limit — at limit",
  "mj.kanban.moveInstructions": "Arrow keys to move, Enter to confirm, Escape to cancel.",
  "mj.kanban.moveCard": "Move card: {title}",
  "mj.kanban.cardMoved": "Card moved to {column}, position {position}.",
  "mj.kanban.movingTo": "Moving card to {column} column, position {position}.",
  "mj.kanban.moveStarted": "Moving card: {title}. Use arrow keys to reposition.",
  "mj.kanban.moveCanceled": "Move canceled.",

  /* mj-master-detail */
  "mj.masterDetail.label": "Master detail view",
  "mj.masterDetail.masterLabel": "List",
  "mj.masterDetail.back": "Back",
  "mj.masterDetail.detailLabel": "Detail",
  "mj.masterDetail.detailItemLabel": "{label}: {item}",
  "mj.masterDetail.detailEmpty": "Select an item to view details.",
  "mj.masterDetail.detailLoading": "Loading…",
  "mj.masterDetail.detailError": "Failed to load details.",
  "mj.masterDetail.resize": "Resize panels",
  "mj.masterDetail.showingDetail": "Showing detail for {item}",

  /* mj-table */
  "mj.table.label": "Table",
  "mj.table.loadingAnnouncement": "Loading table data.",
  "mj.table.empty": "No data",

  /* mj-virtual-list */
  "mj.virtualList.loading": "Loading…",
  "mj.virtualList.loadFailed": "Failed to load items.",
  "mj.virtualList.end": "No more items.",
  "mj.virtualList.loadMore": "Load more",
  "mj.virtualList.empty": "No items",
  "mj.virtualList.endReached": "End of list reached.",
  "mj.virtualList.itemsLoaded": { one: "{count} item loaded.", other: "{count} items loaded." },

  /* mj-calendar */
  "mj.calendar.viewSwitcherLabel": "View",
  "mj.calendar.viewMonth": "Month",
  "mj.calendar.viewWeek": "Week",
  "mj.calendar.viewDay": "Day",
  "mj.calendar.viewAgenda": "Agenda",
  "mj.calendar.gridLabel": "Calendar, {period}",
  "mj.calendar.showingPeriod": "Showing {period}",
  "mj.calendar.showLess": "Show less",
  "mj.calendar.moreEvents": { one: "+{count} more", other: "+{count} more" },
  "mj.calendar.moreEventsLabel": { one: "{count} more event", other: "{count} more events" },
  "mj.calendar.dayWithEvents": { one: "{date}, {count} event", other: "{date}, {count} events" },
  "mj.calendar.eventLabel": "{title}, {time}",
  "mj.calendar.noEvents": "No events",

  /* mj-data-table */
  "mj.dataTable.label": "Data table",
  "mj.dataTable.loadingAnnouncement": "Loading data.",
  "mj.dataTable.loadFailed": "Failed to load data.",
  "mj.dataTable.filterColumn": "Filter {label}",
  "mj.dataTable.editCell": "Edit {label}",
  "mj.dataTable.rowCount": { one: "{count} row", other: "{count} rows" },
  "mj.dataTable.resultCount": { one: "{count} result.", other: "{count} results." },
  "mj.dataTable.sortCleared": "Sort cleared.",
  "mj.dataTable.sortedAscending": "Sorted by {label} ascending.",
  "mj.dataTable.sortedDescending": "Sorted by {label} descending.",

  /* mj-tree-grid */
  "mj.treeGrid.label": "Tree grid",
  "mj.treeGrid.empty": "No data",
  "mj.treeGrid.expandRow": "Expand {label}",
  "mj.treeGrid.collapseRow": "Collapse {label}",
  "mj.treeGrid.rowCollapsed": "{label} collapsed.",
  "mj.treeGrid.rowExpanded": { one: "{label} expanded, {count} child.", other: "{label} expanded, {count} children." },
  "mj.treeGrid.sortCleared": "Sort cleared.",
  "mj.treeGrid.sortedAscending": "Sorted by {label} ascending.",
  "mj.treeGrid.sortedDescending": "Sorted by {label} descending.",

  /* mj-sort-control */
  "mj.sortControl.labelNoneToAsc": "Sort by {label}, not sorted. Activate to sort ascending.",
  "mj.sortControl.labelNoneToDesc": "Sort by {label}, not sorted. Activate to sort descending.",
  "mj.sortControl.labelAscToDesc": "Sort by {label}, sorted ascending. Activate to sort descending.",
  "mj.sortControl.labelAscToNone": "Sort by {label}, sorted ascending. Activate to clear sort.",
  "mj.sortControl.labelDescToAsc": "Sort by {label}, sorted descending. Activate to sort ascending.",
  "mj.sortControl.labelDescToNone": "Sort by {label}, sorted descending. Activate to clear sort.",

  /* mj-row-selector */
  "mj.rowSelector.selectRow": "Select row",
  "mj.rowSelector.selectAllCount": "Select all ({count})",

  /* mj-carousel */
  "mj.carousel.label": "Carousel",
  "mj.carousel.roleDescription": "carousel",
  "mj.carousel.slideRoleDescription": "slide",
  "mj.carousel.previousSlide": "Previous slide",
  "mj.carousel.nextSlide": "Next slide",
  "mj.carousel.chooseSlide": "Choose slide",
  "mj.carousel.slideLabel": "Slide {n} of {total}",
  "mj.carousel.startAutoRotation": "Start auto-rotation",
  "mj.carousel.stopAutoRotation": "Stop auto-rotation",

  /* mj-split-pane */
  "mj.splitPane.resize": "Resize",
  "mj.splitPane.startPaneSize": { one: "Start pane: {size} pixel", other: "Start pane: {size} pixels" },

  /* mj-feed */
  "mj.feed.loadMore": "Load more",
  "mj.feed.newItems": { one: "{count} new item added", other: "{count} new items added" },

  /* mj-card */
  "mj.card.loaded": "Loaded",

  /* mj-hero */
  "mj.hero.pauseVideo": "Pause background video",
  "mj.hero.playVideo": "Play background video",

  /* mj-nav-stepper */
  "mj.navStepper.label": "Progress",
  "mj.navStepper.stepLabel": "Step {n}: {label} – {status}",
  "mj.navStepper.status.complete": "completed",
  "mj.navStepper.status.current": "current",
  "mj.navStepper.status.upcoming": "upcoming",
  "mj.navStepper.status.error": "error",
  "mj.navStepper.status.disabled": "disabled",

  /* mj-wizard */
  "mj.wizard.stepAnnouncement": "Step {n} of {total}: {title}",
  "mj.wizard.stepFallback": "Step {n}",

  /* mj-side-nav */
  "mj.sideNav.expand": "Expand navigation",

  /* mj-tabs */
  "mj.tabs.scrollPrev": "Scroll tabs backward",
  "mj.tabs.scrollNext": "Scroll tabs forward",

  /* mj-pagination */
  "mj.pagination.pageSize": "Items per page",

  /* mj-footer-nav */
  "mj.footerNav.navLabel": "Footer",

  /* mj-dialog */
  "mj.dialog.close": "Close dialog",
  "mj.dialog.confirm": "Confirm",
  "mj.dialog.cancel": "Cancel",
  "mj.dialog.promptLabel": "Enter value",

  /* mj-lightbox */
  "mj.lightbox.label": "Media viewer",
  "mj.lightbox.zoomIn": "Zoom in",
  "mj.lightbox.zoomOut": "Zoom out",
  "mj.lightbox.counter": "{current} of {total}",
  "mj.lightbox.loadError": "This item could not be loaded.",

  /* mj-command-palette */
  "mj.commandPalette.label": "Command palette",
  "mj.commandPalette.placeholder": "Type a command…",
  "mj.commandPalette.empty": "No matching commands",
  "mj.commandPalette.recent": "Recent",
  "mj.commandPalette.resultCount": { one: "{count} command found", other: "{count} commands found" },
  "mj.commandPalette.hintNavigate": "Navigate",
  "mj.commandPalette.hintSelect": "Select",
  "mj.commandPalette.hintDismiss": "Dismiss",

  /* mj-notification-center */
  "mj.notificationCenter.label": "Notifications",
  "mj.notificationCenter.markAllRead": "Mark all read",
  "mj.notificationCenter.clearAll": "Clear all",
  "mj.notificationCenter.empty": "No notifications",
  "mj.notificationCenter.older": "Older",
  "mj.notificationCenter.otherCategory": "Other",
  "mj.notificationCenter.unread": "Unread",
  "mj.notificationCenter.dismiss": "Dismiss",
  "mj.notificationCenter.unreadCount": { one: "{count} unread notification", other: "{count} unread notifications" },
  "mj.notificationCenter.newNotification": "New notification: {title}",

  /* mj-toast-region */
  "mj.toastRegion.label": "Notifications",
  "mj.toastRegion.dismiss": "Dismiss notification",

  /* mj-tour */
  "mj.tour.skip": "Skip tour",
  "mj.tour.back": "Back",
  "mj.tour.next": "Next",
  "mj.tour.done": "Done",
  "mj.tour.counter": "Step {current} of {total}",

  /* mj-context-menu */
  "mj.contextMenu.label": "Actions",
  "mj.contextMenu.popupLabel": "Context menu",

  /* pmchartsupport */
  "mj.pmChart.noData": "No data to display.",
  "mj.pmChart.loadError": "Chart data could not be loaded.",
  "mj.pmChart.showDataTable": "Show data table",

  /* mj-branch-graph */
  "mj.branchGraph.label": "Branch graph",
  "mj.branchGraph.showDataTable": "Show data table",
  "mj.branchGraph.tableCaption": "Branch graph data",
  "mj.branchGraph.columnBranch": "Branch",
  "mj.branchGraph.columnSha": "SHA",
  "mj.branchGraph.columnMessage": "Message",
  "mj.branchGraph.columnAuthor": "Author",
  "mj.branchGraph.columnDate": "Date",
  "mj.branchGraph.noDataLabel": "Branch graph: no data",
  "mj.branchGraph.commitLabel": "Commit {sha}: {message}, {date}",
  "mj.branchGraph.markerLabel": "Milestone {name}, {type}, {date}",
  "mj.branchGraph.defaultMarkerType": "milestone",
  "mj.branchGraph.today": "Today",
  "mj.branchGraph.summary": "Branch graph: {branches}, {commits}, {milestones}",
  "mj.branchGraph.branchCount": { one: "{count} branch", other: "{count} branches" },
  "mj.branchGraph.commitCount": { one: "{count} commit", other: "{count} commits" },
  "mj.branchGraph.milestoneCount": { one: "{count} milestone", other: "{count} milestones" },
  "mj.branchGraph.svgLabel": "{summary}. Use the arrow keys to move between commits and milestones.",
  "mj.branchGraph.detailBranch": "Branch:",
  "mj.branchGraph.detailMessage": "Message:",
  "mj.branchGraph.detailAuthor": "Author:",
  "mj.branchGraph.detailDate": "Date:",
  "mj.branchGraph.detailType": "Type:",
  "mj.branchGraph.commitHeading": "Commit {sha}",

  /* mj-burndown-chart */
  "mj.burndownChart.labelBurndown": "Burndown chart",
  "mj.burndownChart.labelBurnup": "Burnup chart",
  "mj.burndownChart.titleBurndown": "Burndown Chart",
  "mj.burndownChart.titleBurnup": "Burnup Chart",
  "mj.burndownChart.behindSchedule": "Behind schedule",
  "mj.burndownChart.showDataTable": "Show data table",
  "mj.burndownChart.legendIdeal": "Ideal",
  "mj.burndownChart.legendActual": "Actual",
  "mj.burndownChart.legendScopeChange": "Scope change",
  "mj.burndownChart.captionBurndown": "Daily burndown values",
  "mj.burndownChart.captionBurnup": "Daily burnup values",
  "mj.burndownChart.columnDate": "Date",
  "mj.burndownChart.columnRemaining": "Remaining",
  "mj.burndownChart.columnCompleted": "Completed",
  "mj.burndownChart.columnIdeal": "Ideal",
  "mj.burndownChart.columnScopeChange": "Scope Change",
  "mj.burndownChart.defaultUnit": "points",
  "mj.burndownChart.noDataBurndown": "Burndown chart: no data",
  "mj.burndownChart.noDataBurnup": "Burnup chart: no data",
  "mj.burndownChart.axisTitleBurndown": "{unit} remaining",
  "mj.burndownChart.axisTitleBurnup": "{unit} completed",
  "mj.burndownChart.scopeChangeLabel": "Scope change on {date}: {delta} {unit}",
  "mj.burndownChart.today": "Today",
  "mj.burndownChart.pointLabelBurndown": "Day {date}: {value} {unit} remaining, ideal {ideal}",
  "mj.burndownChart.pointLabelBurnup": "Day {date}: {value} {unit} completed, ideal {ideal}",
  "mj.burndownChart.summary": { one: "{title}: {count} day from {start} to {end}, unit: {unit}", other: "{title}: {count} days from {start} to {end}, unit: {unit}" },
  "mj.burndownChart.summaryBehind": { one: "{title}: {count} day from {start} to {end}, unit: {unit}, behind schedule", other: "{title}: {count} days from {start} to {end}, unit: {unit}, behind schedule" },
  "mj.burndownChart.svgLabel": "{summary}. Use the arrow keys to move between data points.",

  /* mj-cumulative-flow */
  "mj.cumulativeFlow.label": "Cumulative flow diagram",
  "mj.cumulativeFlow.title": "Cumulative Flow Diagram",
  "mj.cumulativeFlow.showDataTable": "Show data table",
  "mj.cumulativeFlow.legendLabel": "Workflow states (press to hide or show a state)",
  "mj.cumulativeFlow.tableCaption": "Work items per workflow state by day",
  "mj.cumulativeFlow.columnDate": "Date",
  "mj.cumulativeFlow.noDataLabel": "Cumulative flow diagram: no data",
  "mj.cumulativeFlow.stateCount": { one: "{count} state", other: "{count} states" },
  "mj.cumulativeFlow.stateCountHidden": { one: "{count} state ({hidden} hidden)", other: "{count} states ({hidden} hidden)" },
  "mj.cumulativeFlow.dayCount": { one: "{count} day", other: "{count} days" },
  "mj.cumulativeFlow.summary": "Cumulative flow diagram: {states}, {days} from {start} to {end}",
  "mj.cumulativeFlow.svgLabel": "{summary}. Use the arrow keys to move between days.",
  "mj.cumulativeFlow.stateValue": "{name} {value}",
  "mj.cumulativeFlow.columnLabel": "{date}: {counts}. WIP {wip}",
  "mj.cumulativeFlow.columnLabelLeadTime": { one: "{date}: {counts}. WIP {wip}, approximate lead time {leadTime} day", other: "{date}: {counts}. WIP {wip}, approximate lead time {leadTime} days" },

  /* mj-dependency-graph */
  "mj.dependencyGraph.label": "Dependency graph",
  "mj.dependencyGraph.showList": "Show dependency list",
  "mj.dependencyGraph.noDataLabel": "Dependency graph: no nodes",
  "mj.dependencyGraph.statusTodo": "todo",
  "mj.dependencyGraph.statusInProgress": "in-progress",
  "mj.dependencyGraph.statusDone": "done",
  "mj.dependencyGraph.statusBlocked": "blocked",
  "mj.dependencyGraph.nodeLabel": "{name}, status: {status}",
  "mj.dependencyGraph.nodeLabelCritical": "{label}, on critical path",
  "mj.dependencyGraph.nodeLabelInCycle": "{label}, in cycle",
  "mj.dependencyGraph.summary": "Dependency graph: {nodes}, {edges}",
  "mj.dependencyGraph.nodeCount": { one: "{count} node", other: "{count} nodes" },
  "mj.dependencyGraph.edgeCount": { one: "{count} edge", other: "{count} edges" },
  "mj.dependencyGraph.summaryCriticalPath": { one: "{summary}, critical path: {count} node", other: "{summary}, critical path: {count} nodes" },
  "mj.dependencyGraph.summaryCycles": { one: "{summary}, {count} cycle", other: "{summary}, {count} cycles" },
  "mj.dependencyGraph.svgLabel": "{summary}. Use the arrow keys to move between nodes.",
  "mj.dependencyGraph.cycleDetected": "⚠ Cycle detected: {cycles}",
  "mj.dependencyGraph.dependsOn": "depends on: {names}",
  "mj.dependencyGraph.noDependencies": "no dependencies",
  "mj.dependencyGraph.listTerm": "{name} ({status})",
  "mj.dependencyGraph.detailStatus": "Status:",
  "mj.dependencyGraph.detailEstimate": "Estimate:",

  /* mj-gantt-chart */
  "mj.ganttChart.label": "Gantt chart",
  "mj.ganttChart.showDataTable": "Show data table",
  "mj.ganttChart.tableCaption": "Gantt chart tasks",
  "mj.ganttChart.columnTask": "Task",
  "mj.ganttChart.columnStart": "Start",
  "mj.ganttChart.columnEnd": "End",
  "mj.ganttChart.columnPercent": "% Complete",
  "mj.ganttChart.columnStatus": "Status",
  "mj.ganttChart.noDataLabel": "Gantt chart: no tasks",
  "mj.ganttChart.groupLabelCollapsed": { one: "{name}, group of {count} task, collapsed", other: "{name}, group of {count} tasks, collapsed" },
  "mj.ganttChart.groupLabelExpanded": { one: "{name}, group of {count} task, expanded", other: "{name}, group of {count} tasks, expanded" },
  "mj.ganttChart.noEndDate": "no end date",
  "mj.ganttChart.barLabel": "{name}: {start} to {end}, {percent}% complete",
  "mj.ganttChart.noDates": "No dates",
  "mj.ganttChart.markerLabel": "Milestone {name}, {date}",
  "mj.ganttChart.today": "Today",
  "mj.ganttChart.summary": { one: "Gantt chart: {count} task", other: "Gantt chart: {count} tasks" },
  "mj.ganttChart.svgLabel": "{summary}. Use the arrow keys to move between tasks.",
  "mj.ganttChart.openEnded": "Open-ended",
  "mj.ganttChart.detailStart": "Start:",
  "mj.ganttChart.detailEnd": "End:",
  "mj.ganttChart.detailPercent": "% Complete:",
  "mj.ganttChart.detailStatus": "Status:",
  "mj.ganttChart.detailDate": "Date:",

  /* mj-milestone-timeline */
  "mj.milestoneTimeline.label": "Milestone timeline",
  "mj.milestoneTimeline.showList": "Show accessible list",
  "mj.milestoneTimeline.statePast": "past",
  "mj.milestoneTimeline.stateCurrent": "current",
  "mj.milestoneTimeline.stateUpcoming": "upcoming",
  "mj.milestoneTimeline.defaultType": "milestone",
  "mj.milestoneTimeline.fallbackName": "Marker {number}",
  "mj.milestoneTimeline.noDataLabel": "Milestone timeline: no markers",
  "mj.milestoneTimeline.today": "Today",
  "mj.milestoneTimeline.markerLabel": "{name}, {type}, {date}, {state}",
  "mj.milestoneTimeline.summary": { one: "Milestone timeline: {count} marker", other: "Milestone timeline: {count} markers" },
  "mj.milestoneTimeline.summaryHidden": { one: "Milestone timeline: {count} marker, {hidden} outside the visible range", other: "Milestone timeline: {count} markers, {hidden} outside the visible range" },
  "mj.milestoneTimeline.svgLabel": "{summary}. Use the arrow keys to move between markers.",
  "mj.milestoneTimeline.listItem": "{name}, {type}, {date}",
  "mj.milestoneTimeline.detailType": "Type:",
  "mj.milestoneTimeline.detailDate": "Date:",

  /* mj-velocity-chart */
  "mj.velocityChart.label": "Velocity chart",
  "mj.velocityChart.title": "Velocity Chart",
  "mj.velocityChart.showDataTable": "Show data table",
  "mj.velocityChart.legendCommitted": "Committed",
  "mj.velocityChart.legendCompleted": "Completed",
  "mj.velocityChart.legendAverage": "Rolling Avg",
  "mj.velocityChart.tableCaption": "Sprint velocity data",
  "mj.velocityChart.columnSprint": "Sprint",
  "mj.velocityChart.columnCommitted": "Committed",
  "mj.velocityChart.columnCompleted": "Completed",
  "mj.velocityChart.columnDifference": "Difference",
  "mj.velocityChart.columnAverage": "Rolling Average",
  "mj.velocityChart.fallbackName": "Sprint {number}",
  "mj.velocityChart.statusOnTarget": "On target",
  "mj.velocityChart.statusUnderDelivered": "Under-delivered",
  "mj.velocityChart.statusExceeded": "Exceeded",
  "mj.velocityChart.defaultUnit": "points",
  "mj.velocityChart.noDataLabel": "Velocity chart: no sprints",
  "mj.velocityChart.sprintLabel": "{name}: committed {committed}, completed {completed} {unit}, {status}, rolling average {average}",
  "mj.velocityChart.summary": { one: "Velocity chart: {count} sprint, unit: {unit}, rolling window: {window}", other: "Velocity chart: {count} sprints, unit: {unit}, rolling window: {window}" },
  "mj.velocityChart.svgLabel": "{summary}. Use the arrow keys to move between sprints.",

  /* mj-release-calendar */
  "mj.releaseCalendar.label": "Release calendar",
  "mj.releaseCalendar.previousMonth": "Previous month",
  "mj.releaseCalendar.nextMonth": "Next month",
  "mj.releaseCalendar.previousWeek": "Previous week",
  "mj.releaseCalendar.nextWeek": "Next week",
  "mj.releaseCalendar.today": "Today",
  "mj.releaseCalendar.viewSwitcher": "Calendar view",
  "mj.releaseCalendar.viewMonth": "Month",
  "mj.releaseCalendar.viewWeek": "Week",
  "mj.releaseCalendar.showEventList": "Show event list",
  "mj.releaseCalendar.gridLabel": "Calendar",
  "mj.releaseCalendar.type.release": "release",
  "mj.releaseCalendar.type.freeze": "freeze",
  "mj.releaseCalendar.type.blackout": "blackout",
  "mj.releaseCalendar.type.milestone": "milestone",
  "mj.releaseCalendar.type.holiday": "holiday",
  "mj.releaseCalendar.type.event": "event",
  "mj.releaseCalendar.defaultEventName": "Event {number}",
  "mj.releaseCalendar.noDate": "no date",
  "mj.releaseCalendar.dateRange": "{start} to {end}",
  "mj.releaseCalendar.eventSummary": "{name}, {type}, {date}",
  "mj.releaseCalendar.moreEventsLabel": { one: "{count} more event on {date}", other: "{count} more events on {date}" },
  "mj.releaseCalendar.moreEvents": "+{count} more",
  "mj.releaseCalendar.noEventsCount": "no events",
  "mj.releaseCalendar.eventCount": { one: "{count} event", other: "{count} events" },
  "mj.releaseCalendar.dayLabel": "{date}, {events}",
  "mj.releaseCalendar.dayLabelFreeze": "{date}, {events}, in freeze window",
  "mj.releaseCalendar.noEvents": "No events.",
  "mj.releaseCalendar.typeField": "Type:",
  "mj.releaseCalendar.dateField": "Date:",
  "mj.releaseCalendar.moreInfo": "More info",
  "mj.releaseCalendar.opensInNewTab": "opens in a new tab",

  /* mj-roadmap-chart */
  "mj.roadmapChart.label": "Roadmap chart",
  "mj.roadmapChart.showDataTable": "Show data table",
  "mj.roadmapChart.tableCaption": "Roadmap initiatives",
  "mj.roadmapChart.columnInitiative": "Initiative",
  "mj.roadmapChart.columnSwimlane": "Swimlane",
  "mj.roadmapChart.columnTimeframe": "Column/Timeframe",
  "mj.roadmapChart.columnStatus": "Status",
  "mj.roadmapChart.columnPercent": "% Complete",
  "mj.roadmapChart.status.planned": "planned",
  "mj.roadmapChart.status.inProgress": "in-progress",
  "mj.roadmapChart.status.done": "done",
  "mj.roadmapChart.status.atRisk": "at-risk",
  "mj.roadmapChart.status.blocked": "blocked",
  "mj.roadmapChart.defaultInitiativeName": "Initiative {number}",
  "mj.roadmapChart.quarterLabel": "Q{quarter} {year}",
  "mj.roadmapChart.halfYearLabel": "H{half} {year}",
  "mj.roadmapChart.dateRange": "{start} to {end}",
  "mj.roadmapChart.unassigned": "Unassigned",
  "mj.roadmapChart.noData": "Roadmap: no data",
  "mj.roadmapChart.barLabel": "{name}, {status}, {timeframe}",
  "mj.roadmapChart.milestoneLabel": "Milestone {name}, {date}",
  "mj.roadmapChart.today": "Today",
  "mj.roadmapChart.unplacedReasonBucket": "their column is not one of the buckets",
  "mj.roadmapChart.unplacedReasonDates": "they have no dates inside the visible range",
  "mj.roadmapChart.unplacedNote": { one: "{unplaced} of {count} initiative is not shown on the chart because {reason}. It is listed in the data table.", other: "{unplaced} of {count} initiatives are not shown on the chart because {reason}. They are listed in the data table." },
  "mj.roadmapChart.initiativeCount": { one: "{count} initiative", other: "{count} initiatives" },
  "mj.roadmapChart.swimlaneCount": { one: "{count} swimlane", other: "{count} swimlanes" },
  "mj.roadmapChart.summary": "Roadmap: {initiatives} across {swimlanes}",
  "mj.roadmapChart.svgLabel": "{summary}. Use the arrow keys to move between initiatives.",
  "mj.roadmapChart.notPlaced": "Not placed",
  "mj.roadmapChart.percent": "{percent}%",
  "mj.roadmapChart.statusField": "Status:",
  "mj.roadmapChart.percentField": "% Complete:",
  "mj.roadmapChart.datesField": "Dates:",

  /* mj-env-promotion-chart */
  "mj.envPromotionChart.label": "Environment promotion chart",
  "mj.envPromotionChart.title": "Environment Promotion",
  "mj.envPromotionChart.live": "Live",
  "mj.envPromotionChart.showSummaryList": "Show summary list",
  "mj.envPromotionChart.environments": "Environments",
  "mj.envPromotionChart.health.healthy": "Healthy",
  "mj.envPromotionChart.health.degraded": "Degraded",
  "mj.envPromotionChart.health.down": "Down",
  "mj.envPromotionChart.health.unknown": "Unknown",
  "mj.envPromotionChart.gateStatus.pending": "Pending approval",
  "mj.envPromotionChart.gateStatus.approved": "Approved",
  "mj.envPromotionChart.gateStatus.rejected": "Rejected",
  "mj.envPromotionChart.gateStatus.auto": "Automatic",
  "mj.envPromotionChart.versionChanged": "{name} is now at version {version}",
  "mj.envPromotionChart.pendingAnnouncement": { one: "{count} promotion waiting for approval", other: "{count} promotions waiting for approval" },
  "mj.envPromotionChart.loadError": "Promotion data could not be loaded.",
  "mj.envPromotionChart.noEnvironments": "Environment promotion chart: no environments",
  "mj.envPromotionChart.environmentLabel": "{name}, version: {version}, health: {health}",
  "mj.envPromotionChart.environmentLabelPromoted": "{name}, version: {version}, health: {health}, last promoted {date}",
  "mj.envPromotionChart.promoted": "Promoted {date}",
  "mj.envPromotionChart.gateNamed": "{name} gate",
  "mj.envPromotionChart.gateDefault": "Approval gate",
  "mj.envPromotionChart.gateLabel": "{gate} between {from} and {to}, status: {status}",
  "mj.envPromotionChart.decidePromotion": "Decide promotion to {name}",
  "mj.envPromotionChart.approvePromotion": "Approve promotion to {name}",
  "mj.envPromotionChart.rejectPromotion": "Reject promotion to {name}",
  "mj.envPromotionChart.approve": "Approve",
  "mj.envPromotionChart.reject": "Reject",
  "mj.envPromotionChart.then": "then",
  "mj.envPromotionChart.summary": "Environment promotion chart: {artifact}, {environments}, {pendingGates}",
  "mj.envPromotionChart.artifactFallback": "artifact",
  "mj.envPromotionChart.environmentCount": { one: "{count} environment", other: "{count} environments" },
  "mj.envPromotionChart.pendingGateCount": { one: "{count} pending gate", other: "{count} pending gates" },
  "mj.envPromotionChart.listEnvironment": "{name}: version {version}, health: {health}",
  "mj.envPromotionChart.listEnvironmentPromoted": "{name}: version {version}, health: {health}, last promoted {date}",
  "mj.envPromotionChart.listGate": "{gate} from {from} to {to}: {status}",
  "mj.envPromotionChart.versionField": "Version:",
  "mj.envPromotionChart.healthField": "Health:",
  "mj.envPromotionChart.lastPromotedField": "Last promoted:",
  "mj.envPromotionChart.statusField": "Status:",
  "mj.envPromotionChart.promotionField": "Promotion:",
  "mj.envPromotionChart.promotionRoute": "{from} to {to}",
  "mj.envPromotionChart.gateApproved": "Gate approved",
  "mj.envPromotionChart.gateRejected": "Gate rejected",

  /* mj-build-status-board */
  "mj.buildStatusBoard.status.pending": "Pending",
  "mj.buildStatusBoard.status.running": "Running",
  "mj.buildStatusBoard.status.passed": "Passed",
  "mj.buildStatusBoard.status.failed": "Failed",
  "mj.buildStatusBoard.status.cancelled": "Cancelled",
  "mj.buildStatusBoard.status.skipped": "Skipped",
  "mj.buildStatusBoard.status.unknown": "Unknown",
  "mj.buildStatusBoard.column.pipeline": "Pipeline",
  "mj.buildStatusBoard.column.status": "Status",
  "mj.buildStatusBoard.column.deployTarget": "Deploy target",
  "mj.buildStatusBoard.column.lastRun": "Last run",
  "mj.buildStatusBoard.column.duration": "Duration",
  "mj.buildStatusBoard.column.actor": "Actor",
  "mj.buildStatusBoard.title": "Build Status Board",
  "mj.buildStatusBoard.live": "Live",
  "mj.buildStatusBoard.filterByStatus": "Filter by status",
  "mj.buildStatusBoard.allStatuses": "All statuses",
  "mj.buildStatusBoard.filterByName": "Filter by pipeline name",
  "mj.buildStatusBoard.filterPlaceholder": "Filter by name…",
  "mj.buildStatusBoard.clearFilters": "Clear filters",
  "mj.buildStatusBoard.caption": "Build status board",
  "mj.buildStatusBoard.captionCount": { one: "Build status board: {count} pipeline", other: "Build status board: {count} pipelines" },
  "mj.buildStatusBoard.selectAllFiltered": "Select all filtered pipelines",
  "mj.buildStatusBoard.pipelinesSelected": { one: "{count} pipeline selected", other: "{count} pipelines selected" },
  "mj.buildStatusBoard.selectedCount": "{count} selected",
  "mj.buildStatusBoard.previousPage": "Prev",
  "mj.buildStatusBoard.pageOf": "Page {page} of {total}",
  "mj.buildStatusBoard.groupHeading": "{column}: {value} ({count})",
  "mj.buildStatusBoard.groupNone": "(none)",
  "mj.buildStatusBoard.resultCount": { one: "{count} result", other: "{count} results" },
  "mj.buildStatusBoard.opensInNewTab": "opens in a new tab",
  "mj.buildStatusBoard.selectRow": "Select {name}",
  "mj.buildStatusBoard.durationHours": "{hours}h {minutes}m",
  "mj.buildStatusBoard.durationMinutes": "{minutes}m {seconds}s",
  "mj.buildStatusBoard.durationSeconds": "{seconds}s",
  "mj.buildStatusBoard.statusChanged": "{name} status changed to {status}",
  "mj.buildStatusBoard.noMatch": "No pipelines match the current filters.",

  /* mj-pipeline-chart */
  "mj.pipelineChart.label": "CI pipeline",
  "mj.pipelineChart.showAccessibleList": "Show accessible list",
  "mj.pipelineChart.stageLogs": "Stage logs",
  "mj.pipelineChart.statusLegend": "Status legend",
  "mj.pipelineChart.status.pending": "pending",
  "mj.pipelineChart.status.running": "running",
  "mj.pipelineChart.status.passed": "passed",
  "mj.pipelineChart.status.failed": "failed",
  "mj.pipelineChart.status.cancelled": "cancelled",
  "mj.pipelineChart.status.skipped": "skipped",
  "mj.pipelineChart.gateStatus.pending": "pending",
  "mj.pipelineChart.gateStatus.approved": "approved",
  "mj.pipelineChart.gateStatus.rejected": "rejected",
  "mj.pipelineChart.gateStatus.auto": "auto",
  "mj.pipelineChart.statusChanged": "{name} is now {status}",
  "mj.pipelineChart.defaultGateName": "Gate",
  "mj.pipelineChart.noStages": "CI pipeline: no stages",
  "mj.pipelineChart.stageLabel": "{name} stage, status: {status}",
  "mj.pipelineChart.stageLabelDuration": "{name} stage, status: {status}, {duration}",
  "mj.pipelineChart.gateLabel": "{name} approval gate, status: {status}",
  "mj.pipelineChart.summary": { one: "CI pipeline: {count} stage, status: {status}", other: "CI pipeline: {count} stages, status: {status}" },
  "mj.pipelineChart.svgLabel": "{summary}. Use the arrow keys to move between stages and gates.",
  "mj.pipelineChart.listStage": "{name}: {status}",
  "mj.pipelineChart.listStageDuration": "{name}: {status}, {duration}",
  "mj.pipelineChart.listGate": "{name} approval gate: {status}",
  "mj.pipelineChart.listGateAfter": "{name} approval gate after {stage}: {status}",
  "mj.pipelineChart.stageLogsTitle": "{name} logs",
  "mj.pipelineChart.statusField": "Status:",
  "mj.pipelineChart.afterStageField": "After stage:",
  "mj.pipelineChart.approve": "Approve",
  "mj.pipelineChart.reject": "Reject",
  "mj.pipelineChart.gateTitle": "{name} approval gate",
  "mj.pipelineChart.gateDecided": "{name} approval gate {status}",

  /* mj-workflow-diagram */
  "mj.workflowDiagram.label": "Workflow diagram",
  "mj.workflowDiagram.showAccessibleList": "Show accessible list",
  "mj.workflowDiagram.type.start": "start",
  "mj.workflowDiagram.type.end": "end",
  "mj.workflowDiagram.type.decision": "decision",
  "mj.workflowDiagram.type.state": "state",
  "mj.workflowDiagram.currentStateAnnouncement": "Current state: {name}",
  "mj.workflowDiagram.unassigned": "Unassigned",
  "mj.workflowDiagram.noStates": "Workflow diagram: no states",
  "mj.workflowDiagram.transitionLabel": "Transition from {from} to {to}",
  "mj.workflowDiagram.transitionLabelNamed": "Transition from {from} to {to}: {label}",
  "mj.workflowDiagram.stateLabel": "{name}, type: {type}",
  "mj.workflowDiagram.stateLabelCurrent": "{name}, type: {type}, current state",
  "mj.workflowDiagram.stateCount": { one: "{count} state", other: "{count} states" },
  "mj.workflowDiagram.transitionCount": { one: "{count} transition", other: "{count} transitions" },
  "mj.workflowDiagram.actorCount": { one: "{count} actor", other: "{count} actors" },
  "mj.workflowDiagram.summary": "Workflow diagram: {states}, {transitions}",
  "mj.workflowDiagram.summaryActors": "Workflow diagram: {states}, {transitions}, {actors}",
  "mj.workflowDiagram.svgLabel": "{summary}. Use the arrow keys to move between transitions and states.",
  "mj.workflowDiagram.listTargetNamed": "{name} ({label})",
  "mj.workflowDiagram.listGoesTo": "goes to: {targets}",
  "mj.workflowDiagram.listNoOutgoing": "no outgoing transitions",
  "mj.workflowDiagram.listState": "{name} ({type})",
  "mj.workflowDiagram.typeField": "Type:",
  "mj.workflowDiagram.actorField": "Actor:",
  "mj.workflowDiagram.fromField": "From:",
  "mj.workflowDiagram.toField": "To:",
  "mj.workflowDiagram.labelField": "Label:",
  "mj.workflowDiagram.transitionTitle": "Transition",

  /* mj-app-shell */
  "mj.appShell.statusBarLabel": "Status bar",
  "mj.appShell.secondaryLabel": "Secondary pane",
  "mj.appShell.splitEmpty": "Empty",
  "mj.appShell.appBarLabel": "App bar",
  "mj.appShell.mainLabel": "Main content",
  "mj.appShell.focusMoved": "Focus moved to {name}",
  "mj.appShell.resizeNav": "Resize navigation",
  "mj.appShell.resizeInspector": "Resize inspector",
  "mj.appShell.resizePanes": "Resize panes",
  "mj.appShell.sizePixels": { one: "{count} pixel", other: "{count} pixels" },
  "mj.appShell.sizePercent": { one: "{count} percent", other: "{count} percent" },

  /* mj-filter-panel */
  "mj.filterPanel.label": "Filters",
  "mj.filterPanel.appliedFilters": "Applied filters",
  "mj.filterPanel.sortBy": "Sort by",
  "mj.filterPanel.sortAscending": "Sort ascending",
  "mj.filterPanel.sortDescending": "Sort descending",
  "mj.filterPanel.defaultSort": "Default",
  "mj.filterPanel.noOptions": "No options available",
  "mj.filterPanel.selectedCount": { one: "{count} selected", other: "{count} selected" },
  "mj.filterPanel.removeFilter": "Remove {label}",
  "mj.filterPanel.clearAll": "Clear all",
  "mj.filterPanel.resultCount": { one: "Showing {countText} result", other: "Showing {countText} results" },

  /* mj-menu */
  "mj.menu.empty": "No options",

  /* mj-menubar */
  "mj.menubar.label": "Application menu",
  "mj.menubar.noItems": "No items",

  /* mj-query-builder */
  "mj.queryBuilder.label": "Query builder",
  "mj.queryBuilder.expressionLabel": "Query expression",
  "mj.queryBuilder.incomplete": "One or more conditions are incomplete.",
  "mj.queryBuilder.empty": "Add at least one condition.",
  "mj.queryBuilder.ruleIncomplete": "Condition is incomplete",
  "mj.queryBuilder.groupLabel": "Condition group, {combinator}",
  "mj.queryBuilder.combineWith": "Combine conditions with",
  "mj.queryBuilder.combinatorAnd": "AND",
  "mj.queryBuilder.combinatorOr": "OR",
  "mj.queryBuilder.combinatorChanged": "Group operator changed to {combinator}",
  "mj.queryBuilder.removeGroup": "Remove group",
  "mj.queryBuilder.removeGroupLabel": "Remove condition group",
  "mj.queryBuilder.emptyGroup": "Add a condition",
  "mj.queryBuilder.addCondition": "Add condition",
  "mj.queryBuilder.addGroup": "Add group",
  "mj.queryBuilder.ruleLabel": "Condition {number}",
  "mj.queryBuilder.removeRuleLabel": "Remove condition {number}",
  "mj.queryBuilder.field": "Field",
  "mj.queryBuilder.noFields": "No fields configured",
  "mj.queryBuilder.selectField": "Select field…",
  "mj.queryBuilder.operator": "Operator",
  "mj.queryBuilder.selectOperator": "Select operator…",
  "mj.queryBuilder.value": "Value",
  "mj.queryBuilder.values": "Values",
  "mj.queryBuilder.valuesList": "Values, separated by commas",
  "mj.queryBuilder.rangeFrom": "From",
  "mj.queryBuilder.rangeTo": "To",
  "mj.queryBuilder.selectValue": "Select value…",
  "mj.queryBuilder.groupRemoved": "Condition group removed",
  "mj.queryBuilder.ruleRemoved": "Condition removed",
  "mj.queryBuilder.operatorEquals": "equals",
  "mj.queryBuilder.operatorContains": "contains",
  "mj.queryBuilder.operatorStartsWith": "starts with",
  "mj.queryBuilder.operatorEndsWith": "ends with",
  "mj.queryBuilder.operatorIsEmpty": "is empty",
  "mj.queryBuilder.operatorIsNotEmpty": "is not empty",
  "mj.queryBuilder.operatorIsBetween": "is between",
  "mj.queryBuilder.operatorIs": "is",
  "mj.queryBuilder.operatorIsBefore": "is before",
  "mj.queryBuilder.operatorIsAfter": "is after",
  "mj.queryBuilder.operatorIsTrue": "is true",
  "mj.queryBuilder.operatorIsFalse": "is false",
  "mj.queryBuilder.operatorIsNot": "is not",
  "mj.queryBuilder.operatorIsAnyOf": "is any of",

  /* mj-search-results */
  "mj.searchResults.listLabel": "Search results",
  "mj.searchResults.loadMore": "Load more",
  "mj.searchResults.count": { one: "{countText} result", other: "{countText} results" },
  "mj.searchResults.empty": "No results found.",
  "mj.searchResults.loadError": "Results could not be loaded.",

  /* mj-status-bar */
  "mj.statusBar.label": "Status bar",

  /* mj-toolbar */
  "mj.toolbar.moreActions": "More actions",

  /* mj-activity-feed */
  "mj.activityFeed.label": "Activity feed",
  "mj.activityFeed.loadError": "Activity could not be loaded.",
  "mj.activityFeed.retry": "Retry",
  "mj.activityFeed.loadOlder": "Load older activity",
  "mj.activityFeed.allLoaded": "All activity loaded",
  "mj.activityFeed.empty": "No activity yet.",
  "mj.activityFeed.showMore": "Show more",
  "mj.activityFeed.showLess": "Show less",
  "mj.activityFeed.systemActor": "System",
  "mj.activityFeed.newEventsBanner": { one: "{count} new event. Click to view.", other: "{count} new events. Click to view." },
  "mj.activityFeed.newActivities": { one: "{count} new activity", other: "{count} new activities" },

  /* mj-chat-composer */
  "mj.chatComposer.label": "Message composer",
  "mj.chatComposer.placeholder": "Type a message…",
  "mj.chatComposer.replyPreviewLabel": "Replying to message",
  "mj.chatComposer.replyingTo": "Replying to: {preview}",
  "mj.chatComposer.replyTargetFallback": "message",
  "mj.chatComposer.cancelReply": "Cancel reply",
  "mj.chatComposer.attachmentsLabel": "Attachments",
  "mj.chatComposer.emojiPanelLabel": "Emoji",
  "mj.chatComposer.insertEmojiOption": "Insert {emoji}",
  "mj.chatComposer.attachFile": "Attach file",
  "mj.chatComposer.insertEmoji": "Insert emoji",
  "mj.chatComposer.sendMessage": "Send message",
  "mj.chatComposer.sending": "Sending…",
  "mj.chatComposer.send": "Send",
  "mj.chatComposer.tooLong": { one: "Message is longer than {count} character", other: "Message is longer than {count} characters" },
  "mj.chatComposer.typeNotAllowed": "File type not allowed",
  "mj.chatComposer.tooLarge": "Too large (max {size})",
  "mj.chatComposer.notAttached": { one: "{count} file could not be attached", other: "{count} files could not be attached" },
  "mj.chatComposer.removeAttachment": "Remove attachment {name}",
  "mj.chatComposer.dismissRejected": "Dismiss {name}: {reason}",
  "mj.chatComposer.uploading": "Uploading {name}",
  "mj.chatComposer.uploadError": "Error",

  /* mj-chat-message */
  "mj.chatMessage.attachmentsLabel": "Attachments",
  "mj.chatMessage.actionsLabel": "Message actions",
  "mj.chatMessage.messageFrom": "Message from {name}",
  "mj.chatMessage.status.sent": "Sent",
  "mj.chatMessage.status.delivered": "Delivered",
  "mj.chatMessage.status.read": "Read",
  "mj.chatMessage.status.failed": "Failed to send",
  "mj.chatMessage.attachmentFallbackName": "Attachment",
  "mj.chatMessage.reactWith": { one: "React with {emoji}, {count} reaction", other: "React with {emoji}, {count} reactions" },
  "mj.chatMessage.reply": "Reply",
  "mj.chatMessage.copyText": "Copy text",
  "mj.chatMessage.retry": "Retry",
  "mj.chatMessage.edit": "Edit",
  "mj.chatMessage.delete": "Delete",

  /* mj-comments */
  "mj.comments.label": "Comments",
  "mj.comments.count": { one: "{count} comment", other: "{count} comments" },
  "mj.comments.loadEarlier": "Load earlier comments",
  "mj.comments.loadError": "Comments could not be loaded.",
  "mj.comments.retry": "Retry",
  "mj.comments.placeholder": "Write a comment…",
  "mj.comments.newCommentLabel": "New comment",
  "mj.comments.postCommentLabel": "Post comment",
  "mj.comments.post": "Post",
  "mj.comments.postError": "Your comment could not be posted. Try again.",
  "mj.comments.postErrorAnnouncement": "Your comment could not be posted.",
  "mj.comments.empty": "Be the first to comment.",
  "mj.comments.deletedPlaceholder": "[Comment deleted]",
  "mj.comments.editCommentLabel": "Edit comment",
  "mj.comments.cancel": "Cancel",
  "mj.comments.saveEditLabel": "Save edit",
  "mj.comments.save": "Save",
  "mj.comments.reactionChipLabel": { one: "React with {emoji}, {count} reaction", other: "React with {emoji}, {count} reactions" },
  "mj.comments.addReaction": "Add reaction",
  "mj.comments.chooseReaction": "Choose a reaction",
  "mj.comments.reactWith": "React with {emoji}",
  "mj.comments.replyToComment": "Reply to comment",
  "mj.comments.reply": "Reply",
  "mj.comments.edit": "Edit",
  "mj.comments.deleteCommentLabel": "Delete comment",
  "mj.comments.delete": "Delete",
  "mj.comments.replyPlaceholder": "Write a reply…",
  "mj.comments.replyToAuthor": "Reply to {name}",
  "mj.comments.replyTargetFallback": "comment",
  "mj.comments.postReplyLabel": "Post reply",
  "mj.comments.unknownAuthor": "Unknown",
  "mj.comments.repliesTo": "Replies to {name}",
  "mj.comments.showMoreReplies": { one: "Show {count} more reply", other: "Show {count} more replies" },
  "mj.comments.updated": "Comment updated",
  "mj.comments.deleteConfirm": "Delete this comment?",
  "mj.comments.deleted": "Comment deleted",

  /* mj-dropzone */
  "mj.dropzone.label": "File upload",
  "mj.dropzone.browse": "Browse files",
  "mj.dropzone.dragLabel": "Drag and drop files here, or",
  "mj.dropzone.selectedFilesLabel": "Selected files",
  "mj.dropzone.rejectedFilesLabel": "Rejected files",
  "mj.dropzone.maxSizePerFile": "Max {size} per file",
  "mj.dropzone.typeNotAllowed": "File type not allowed: {type}",
  "mj.dropzone.unknownType": "unknown",
  "mj.dropzone.tooLarge": "File too large: {size} (max {max})",
  "mj.dropzone.onlyOneFile": "Only one file can be selected",
  "mj.dropzone.maxFilesExceeded": "Maximum file count exceeded",
  "mj.dropzone.rejectedAnnouncement": { one: "{count} file rejected", other: "{count} files rejected" },
  "mj.dropzone.addedAnnouncement": { one: "{count} file added", other: "{count} files added" },
  "mj.dropzone.removeFile": "Remove {name}",
  "mj.dropzone.uploading": "Uploading {name}",
  "mj.dropzone.uploadComplete": "Upload complete",
  "mj.dropzone.uploadError": "Error",
  "mj.dropzone.dismissError": "Dismiss error for {name}",
  "mj.dropzone.required": "Please select a file.",
  "mj.dropzone.uploadedAnnouncement": "{name} uploaded",
  "mj.dropzone.uploadFailedAnnouncement": "{name}: {error}",
  "mj.dropzone.removedAnnouncement": "{name} removed",

  /* mj-file-browser */
  "mj.fileBrowser.label": "File browser",
  "mj.fileBrowser.pathLabel": "File path",
  "mj.fileBrowser.listView": "List view",
  "mj.fileBrowser.gridView": "Grid view",
  "mj.fileBrowser.foldersLabel": "Folders",
  "mj.fileBrowser.filesLabel": "Files",
  "mj.fileBrowser.previewLabel": "File preview",
  "mj.fileBrowser.itemCount": { one: "{count} item", other: "{count} items" },
  "mj.fileBrowser.selectedCount": { one: "{count} selected", other: "{count} selected" },
  "mj.fileBrowser.itemsSelected": { one: "{count} item selected", other: "{count} items selected" },
  "mj.fileBrowser.panelTree": "Folder tree",
  "mj.fileBrowser.panelFiles": "Files",
  "mj.fileBrowser.panelPreview": "Preview",
  "mj.fileBrowser.focusMoved": "Focus moved to {panel}",
  "mj.fileBrowser.loadFailed": "Failed to load directory",
  "mj.fileBrowser.retry": "Retry",
  "mj.fileBrowser.noFiles": "No files",
  "mj.fileBrowser.emptyFolder": "No files in this folder",
  "mj.fileBrowser.columnName": "Name",
  "mj.fileBrowser.columnSize": "Size",
  "mj.fileBrowser.columnModified": "Modified",
  "mj.fileBrowser.previewHint": "Select a file to preview",
  "mj.fileBrowser.previewType": "Type: {type}",
  "mj.fileBrowser.unknownType": "unknown",
  "mj.fileBrowser.previewSize": "Size: {size}",
  "mj.fileBrowser.previewModified": "Modified: {modified}",

  /* mj-mention-input */
  "mj.mentionInput.suggestionsLabel": "Suggestions",
  "mj.mentionInput.noMatches": "No matches",
  "mj.mentionInput.suggestionsAvailable": "Suggestions available. Use arrow key to navigate.",
  "mj.mentionInput.tooLong": { one: "The value must be {count} character or fewer.", other: "The value must be {count} characters or fewer." },
  "mj.mentionInput.maxLengthReached": { one: "Maximum length of {count} character reached", other: "Maximum length of {count} characters reached" },

  /* mj-cascading-select */
  "mj.cascadingSelect.placeholder": "Select...",
  "mj.cascadingSelect.loadError": "Failed to load options",
  "mj.cascadingSelect.retry": "Retry",
  "mj.cascadingSelect.loadingLevel": "Loading {label} options",
  "mj.cascadingSelect.levelLabel": "Level {level}",
  "mj.cascadingSelect.levelsRequired": "All levels must be selected.",

  /* mj-checkbox-group */
  "mj.checkboxGroup.selectionRequired": "At least one option must be selected.",

  /* mj-combobox */
  "mj.combobox.toggleSuggestions": "Toggle suggestions",
  "mj.combobox.loadError": "Failed to load options",

  /* mj-listbox */
  "mj.listbox.selectedCount": { one: "{count} item selected", other: "{count} items selected" },
  "mj.listbox.selectionRequired": "At least one selection is required.",

  /* mj-menu-button */
  "mj.menuButton.defaultLabel": "Actions",

  /* mj-split-button */
  "mj.splitButton.moreActions": "More actions",
  "mj.splitButton.defaultChanged": "Default action changed to {label}",

  /* mj-asset-picker */
  "mj.assetPicker.triggerLabel": "Asset picker",
  "mj.assetPicker.triggerLabelCurrent": "Asset picker, current: {labels}",
  "mj.assetPicker.dialogLabel": "Choose an asset",
  "mj.assetPicker.searchLabel": "Search assets",
  "mj.assetPicker.categoriesLabel": "Categories",
  "mj.assetPicker.gridLabel": "Assets",
  "mj.assetPicker.allCategories": "All",
  "mj.assetPicker.results": { one: "{count} result", other: "{count} results" },
  "mj.assetPicker.resultsForQuery": { one: "{count} result for {query}", other: "{count} results for {query}" },

  /* mj-color-picker */
  "mj.colorPicker.triggerLabel": "Color picker",
  "mj.colorPicker.triggerLabelCurrent": "Color picker, current color: {color}",
  "mj.colorPicker.dialogLabel": "Choose a color",
  "mj.colorPicker.canvasLabel": "Saturation and brightness",
  "mj.colorPicker.canvasValueText": "Saturation {saturation}%, brightness {brightness}%",
  "mj.colorPicker.hueLabel": "Hue",
  "mj.colorPicker.hueValueText": { one: "{count} degree", other: "{count} degrees" },
  "mj.colorPicker.alphaLabel": "Opacity",
  "mj.colorPicker.valueLabel": "Color value",
  "mj.colorPicker.eyedropper": "Pick",
  "mj.colorPicker.eyedropperLabel": "Pick a color from the screen",
  "mj.colorPicker.swatchesLabel": "Swatches",
  "mj.colorPicker.colorUpdated": "Color updated: {color}",

  /* mj-date-picker */
  "mj.datePicker.clearDate": "Clear date",
  "mj.datePicker.clearTime": "Clear time",
  "mj.datePicker.openCalendar": "Open calendar",
  "mj.datePicker.openTimePicker": "Open time picker",
  "mj.datePicker.chooseDate": "Choose a date",
  "mj.datePicker.chooseTime": "Choose a time",
  "mj.datePicker.previousYear": "Previous year",
  "mj.datePicker.previousMonth": "Previous month",
  "mj.datePicker.nextMonth": "Next month",
  "mj.datePicker.nextYear": "Next year",
  "mj.datePicker.hour": "Hour",
  "mj.datePicker.minute": "Minute",
  "mj.datePicker.hourPlaceholder": "HH",
  "mj.datePicker.minutePlaceholder": "MM",
  "mj.datePicker.done": "Done",
  "mj.datePicker.selectDate": "Select date",
  "mj.datePicker.selectTime": "Select time",
  "mj.datePicker.todayLabel": "{date}, today",
  "mj.datePicker.invalidDate": "Enter a valid date.",

  /* mj-file-picker */
  "mj.filePicker.dropzoneRegion": "File upload dropzone",
  "mj.filePicker.dropzoneLabel": "Drag files here or",
  "mj.filePicker.chooseFiles": "Choose files",
  "mj.filePicker.dropHere": "Drop files here to upload",
  "mj.filePicker.typeError": "{name} is not an accepted file type.",
  "mj.filePicker.sizeError": "{name} exceeds maximum file size.",
  "mj.filePicker.countError": "Maximum number of files ({max}) reached.",
  "mj.filePicker.statusUploading": "Uploading…",
  "mj.filePicker.statusUploaded": "Uploaded",
  "mj.filePicker.statusFailed": "Upload failed",
  "mj.filePicker.progressLabel": "{name} upload progress",
  "mj.filePicker.retry": "Retry",
  "mj.filePicker.retryLabel": "Retry upload of {name}",
  "mj.filePicker.uploaded": "{name} uploaded",
  "mj.filePicker.uploadFailed": "{name} upload failed",

  /* mj-locale-picker */
  "mj.localePicker.clearSelection": "Clear selection",
  "mj.localePicker.showOptions": "Show options",
  "mj.localePicker.hideOptions": "Hide options",
  "mj.localePicker.selectLanguage": "Select a language",
  "mj.localePicker.selectCountry": "Select a country",
  "mj.localePicker.selectLocale": "Select a locale",
  "mj.localePicker.languages": "Languages",
  "mj.localePicker.countries": "Countries",
  "mj.localePicker.locales": "Locales",
  "mj.localePicker.noResultsFound": "No results found",

  /* mj-tag-picker */
  "mj.tagPicker.label": "Tag picker",
  "mj.tagPicker.suggestionsLabel": "Suggestions",
  "mj.tagPicker.loading": "Loading…",
  "mj.tagPicker.loadError": "Failed to load suggestions.",
  "mj.tagPicker.noResults": "No results found.",
  "mj.tagPicker.removeToken": "Remove {label}",
  "mj.tagPicker.maxReached": { one: "Maximum {count} tag reached.", other: "Maximum {count} tags reached." },
  "mj.tagPicker.tokenAdded": { one: "{label} added. {count} tag selected.", other: "{label} added. {count} tags selected." },
  "mj.tagPicker.tokenRemoved": { one: "{label} removed. {count} tag selected.", other: "{label} removed. {count} tags selected." },

  /* mj-transfer-list */
  "mj.transferList.sourceLabel": "Available",
  "mj.transferList.targetLabel": "Selected",
  "mj.transferList.count": { one: "{count} item", other: "{count} items" },
  "mj.transferList.emptySource": "No available items.",
  "mj.transferList.emptyTarget": "No selected items.",
  "mj.transferList.controlsLabel": "Move controls",
  "mj.transferList.moveUp": "Move up",
  "mj.transferList.moveDown": "Move down",
  "mj.transferList.moveSelectedTo": "Move selected to {label}",
  "mj.transferList.moveAllTo": "Move all to {label}",
  "mj.transferList.filterPlaceholder": "Filter {label}…",
  "mj.transferList.filterLabel": "Filter {label}",
  "mj.transferList.maxReached": { one: "Maximum {count} item reached in {label}.", other: "Maximum {count} items reached in {label}." },
  "mj.transferList.moved": { one: "{count} item moved to {label}.", other: "{count} items moved to {label}." },
  "mj.transferList.contains": { one: "{label} now contains {count} item.", other: "{label} now contains {count} items." },

  /* mj-tree-selector */
  "mj.treeSelector.label": "Tree",
  "mj.treeSelector.empty": "No items.",
  "mj.treeSelector.loading": "Loading…",
  "mj.treeSelector.expanded": "{label} expanded",
  "mj.treeSelector.collapsed": "{label} collapsed",
  "mj.treeSelector.loadingChildren": "Loading {label} children",
  "mj.treeSelector.loaded": { one: "Loaded {count} item", other: "Loaded {count} items" },

  /* mj-captcha */
  "mj.captcha.groupLabel": "Security verification",
  "mj.captcha.unavailable": "Security verification is not available. Please try again later or contact support.",
  "mj.captcha.providerFailed": "Provider failed to load.",
  "mj.captcha.notReady": "Security verification is still loading. Please try again in a moment.",
  "mj.captcha.verifying": "Verifying…",
  "mj.captcha.verificationFailed": "Verification failed.",
  "mj.captcha.verified": "Verification successful",
  "mj.captcha.expired": "Verification expired, please try again",
  "mj.captcha.required": "Please complete the security verification.",

  /* mj-masked-input */
  "mj.maskedInput.incomplete": "Please complete the required format.",

  /* mj-number-field */
  "mj.numberField.increase": "Increase",
  "mj.numberField.decrease": "Decrease",
  "mj.numberField.badInput": "Please enter a number.",
  "mj.numberField.rangeUnderflow": "Value must be {min} or more.",
  "mj.numberField.rangeOverflow": "Value must be {max} or less.",

  /* mj-otp-input */
  "mj.otpInput.digitLabel": "Digit {position} of {length}",
  "mj.otpInput.characterLabel": "Character {position} of {length}",
  "mj.otpInput.groupLabel": "Verification code",
  "mj.otpInput.complete": "Code entered",
  "mj.otpInput.incomplete": "Please complete the verification code.",

  /* mj-password-field */
  "mj.passwordField.showPassword": "Show password",
  "mj.passwordField.strengthMeter": "Password strength",
  "mj.passwordField.strength.veryWeak": "Very weak",
  "mj.passwordField.strength.weak": "Weak",
  "mj.passwordField.strength.fair": "Fair",
  "mj.passwordField.strength.strong": "Strong",
  "mj.passwordField.capsLock": "Caps Lock is on",
  "mj.passwordField.tooShort": { one: "Password must be at least {count} character.", other: "Password must be at least {count} characters." },
  "mj.passwordField.tooLong": { one: "Password must be at most {count} character.", other: "Password must be at most {count} characters." },

  /* mj-rating */
  "mj.rating.starItem": { one: "{count} star out of {max}", other: "{count} stars out of {max}" },
  "mj.rating.heartItem": { one: "{count} heart out of {max}", other: "{count} hearts out of {max}" },
  "mj.rating.pointItem": { one: "{count} point out of {max}", other: "{count} points out of {max}" },
  "mj.rating.diamondItem": { one: "{count} diamond out of {max}", other: "{count} diamonds out of {max}" },
  "mj.rating.starRated": { one: "{value} out of {max} star", other: "{value} out of {max} stars" },
  "mj.rating.heartRated": { one: "{value} out of {max} heart", other: "{value} out of {max} hearts" },
  "mj.rating.pointRated": { one: "{value} out of {max} point", other: "{value} out of {max} points" },
  "mj.rating.diamondRated": { one: "{value} out of {max} diamond", other: "{value} out of {max} diamonds" },
  "mj.rating.valueLabel": "{value} out of {max}",
  "mj.rating.rated": "Rated {rating}",
  "mj.rating.groupLabel": "Rating",
  "mj.rating.required": "Please select a rating.",

  /* mj-search-input */
  "mj.searchInput.clear": "Clear search",
  "mj.searchInput.loadingSuggestions": "Loading suggestions…",
  "mj.searchInput.tooLong": { one: "Please use at most {count} character (currently {current}).", other: "Please use at most {count} characters (currently {current})." },

  /* mj-slider */
  "mj.slider.minimum": "Minimum",
  "mj.slider.maximum": "Maximum",
  "mj.slider.minimumNamed": "Minimum {name}",
  "mj.slider.maximumNamed": "Maximum {name}",
  "mj.slider.value": "Value",

  /* mj-textarea */
  "mj.textarea.wordCount": { one: "{count} word", other: "{count} words" },
  "mj.textarea.tooShort": { one: "Please use at least {count} character (currently {current}).", other: "Please use at least {count} characters (currently {current})." },
  "mj.textarea.tooLong": { one: "Please use at most {count} character (currently {current}).", other: "Please use at most {count} characters (currently {current})." },

  /* mj-text-field */
  "mj.textField.tooShort": { one: "Please use at least {count} character (currently {current}).", other: "Please use at least {count} characters (currently {current})." },
  "mj.textField.tooLong": { one: "Please use at most {count} character (currently {current}).", other: "Please use at most {count} characters (currently {current})." },
  "mj.textField.patternMismatch": "Please match the requested format.",

  /* mj-token-input */
  "mj.tokenInput.maxReached": { one: "Maximum {count} tag reached", other: "Maximum {count} tags reached" },
  "mj.tokenInput.addTag": "Add tag",
  "mj.tokenInput.groupLabel": "Token input",
  "mj.tokenInput.selectedTags": "{name}: selected tags",
  "mj.tokenInput.required": "At least one tag is required.",
  "mj.tokenInput.duplicate": "{value} is already added",
  "mj.tokenInput.notInList": "Choose a value from the list.",
  "mj.tokenInput.invalidValue": "Invalid value",
  "mj.tokenInput.added": "{value} added",
  "mj.tokenInput.removed": "{value} removed",
  "mj.tokenInput.removeToken": "Remove {token}",
  "mj.tokenInput.loadingSuggestions": "Loading suggestions…",

  /* mj-typed-field */
  "mj.typedField.invalidEmail": "Please enter a valid email address.",
  "mj.typedField.invalidUrl": "Please enter a valid URL (e.g., https://example.com).",
  "mj.typedField.invalidTel": "Please enter a valid telephone number.",
  "mj.typedField.urlMissingScheme": "Please enter a full URL starting with https://.",
  "mj.typedField.tooShort": { one: "Please use at least {count} character (currently {current}).", other: "Please use at least {count} characters (currently {current})." },
  "mj.typedField.tooLong": { one: "Please use at most {count} character (currently {current}).", other: "Please use at most {count} characters (currently {current})." },
  "mj.typedField.patternMismatch": "Please match the requested format.",

  /* mj-character-counter */
  "mj.characterCounter.charactersRemaining": { one: "{countText} character remaining", other: "{countText} characters remaining" },
  "mj.characterCounter.wordsRemaining": { one: "{countText} word remaining", other: "{countText} words remaining" },
  "mj.characterCounter.unitRemaining": "{countText} {unit} remaining",
  "mj.characterCounter.charactersExceeded": { one: "{countText} character over the limit", other: "{countText} characters over the limit" },
  "mj.characterCounter.wordsExceeded": { one: "{countText} word over the limit", other: "{countText} words over the limit" },
  "mj.characterCounter.unitExceeded": "{countText} {unit} over the limit",

  /* mj-code-editor */
  "mj.codeEditor.label": "Code editor",
  "mj.codeEditor.keyboardHint": "Tab indents. Press Escape, then Tab, to move focus out of the editor.",
  "mj.codeEditor.exitAnnouncement": "Press Tab to move focus out of the code editor.",
  "mj.codeEditor.minLength": { one: "Enter at least {count} character.", other: "Enter at least {count} characters." },
  "mj.codeEditor.maxLength": { one: "Enter no more than {count} character.", other: "Enter no more than {count} characters." },

  /* mj-fieldset */
  "mj.fieldset.optional": "(optional)",

  /* mj-form */
  "mj.form.submitting": "Submitting…",

  /* mj-inline-edit */
  "mj.inlineEdit.edit": "Edit",
  "mj.inlineEdit.editValue": "Edit value",
  "mj.inlineEdit.save": "Save",
  "mj.inlineEdit.cancel": "Cancel",
  "mj.inlineEdit.minLength": { one: "Minimum {count} character required.", other: "Minimum {count} characters required." },
  "mj.inlineEdit.maxLength": { one: "Maximum {count} character allowed.", other: "Maximum {count} characters allowed." },
  "mj.inlineEdit.patternMismatch": "Value does not match the required format.",

  /* mj-label */
  "mj.label.optional": "(optional)",

  /* mj-markdown-editor */
  "mj.markdownEditor.label": "Markdown editor",
  "mj.markdownEditor.toolbarLabel": "Markdown formatting",
  "mj.markdownEditor.viewModeLabel": "View mode",
  "mj.markdownEditor.previewLabel": "Preview",
  "mj.markdownEditor.viewEdit": "Edit",
  "mj.markdownEditor.viewSplit": "Split",
  "mj.markdownEditor.viewPreview": "Preview",
  "mj.markdownEditor.bold": "Bold",
  "mj.markdownEditor.italic": "Italic",
  "mj.markdownEditor.link": "Link",
  "mj.markdownEditor.heading1": "Heading 1",
  "mj.markdownEditor.heading2": "Heading 2",
  "mj.markdownEditor.bullet": "Bullet",
  "mj.markdownEditor.numbered": "Numbered",
  "mj.markdownEditor.blockquote": "Blockquote",
  "mj.markdownEditor.code": "Code",
  "mj.markdownEditor.wordCount": { one: "{count} word", other: "{count} words" },
  "mj.markdownEditor.minLength": { one: "Enter at least {count} character.", other: "Enter at least {count} characters." },
  "mj.markdownEditor.maxLength": { one: "Enter no more than {count} character.", other: "Enter no more than {count} characters." },

  /* mj-rich-text-editor */
  "mj.richTextEditor.label": "Rich text editor",
  "mj.richTextEditor.toolbarLabel": "Formatting",
  "mj.richTextEditor.textStyle": "Text style",
  "mj.richTextEditor.lists": "Lists",
  "mj.richTextEditor.blocks": "Blocks",
  "mj.richTextEditor.bold": "Bold",
  "mj.richTextEditor.italic": "Italic",
  "mj.richTextEditor.underline": "Underline",
  "mj.richTextEditor.strikethrough": "Strikethrough",
  "mj.richTextEditor.bulletList": "Bullet list",
  "mj.richTextEditor.numberedList": "Numbered list",
  "mj.richTextEditor.heading2": "Heading 2",
  "mj.richTextEditor.heading3": "Heading 3",
  "mj.richTextEditor.blockquote": "Blockquote",
  "mj.richTextEditor.maxLength": { one: "Content must be {count} character or fewer.", other: "Content must be {count} characters or fewer." },

  /* mj-validation-summary */
  "mj.validationSummary.heading": { one: "{count} error prevented this form from being submitted", other: "{count} errors prevented this form from being submitted" }
};

const overrides = {};

/* Callbacks registered through `onLocaleChange`. */
const localeListeners = [];

/*
 * Tell every listener that the locale or the string table changed, and fire
 * `mj-locale-change` (detail: { locale }) on the document for application
 * code. Each listener runs in a microtask of its own, so one component
 * failing to render again neither stops the others nor the caller.
 */
function notifyLocaleChange() {
  const listeners = localeListeners.slice()
  const locale = currentLocale

  for (let index = 0; index < listeners.length; index = index + 1) {
    const listener = listeners[index]
    queueMicrotask(() => {
      if (localeListeners.includes(listener) === true) {
        listener(locale)
      }
    })
  }

  if (typeof document !== "undefined") {
    document.dispatchEvent(new CustomEvent("mj-locale-change", { detail: { locale: locale } }))
  }
  return
}

/*
 * Call `listener(locale)` after every locale or string-table change. Returns
 * a function that removes the listener again. MjElement subscribes every
 * connected component, so components render again in the new locale.
 */
export function onLocaleChange(listener) {
  localeListeners.push(listener)
  const unsubscribe = () => {
    const index = localeListeners.indexOf(listener)
    if (index >= 0) {
      localeListeners.splice(index, 1)
    }
  }
  return unsubscribe
}

/*
 * Switch the locale used by `t()` plural rules and the format helpers.
 * Connected components render again when the locale actually changes.
 */
export function setLocale(locale) {
  if (locale !== currentLocale) {
    currentLocale = locale
    notifyLocaleChange()
  }
  return
}

export function getLocale() {
  return currentLocale
}

/*
 * Resolve a localized string by key. `params` values replace {name} tokens.
 */
export function t(key, params) {
  let template = overrides[key]
  if (template === undefined) {
    template = STRINGS[key]
  }
  if (template === undefined) {
    template = key
  }
  if (template !== null && typeof template === "object") {
    template = selectPluralForm(template, params)
  }

  /*
   * One pass over the template: a value that itself contains "{name}" text
   * (a file name, a user's label) is inserted as is and never re-filled.
   * Tokens without a matching param stay in the text.
   */
  let result = template
  if (params !== null && params !== undefined) {
    result = template.replace(/\{([A-Za-z0-9_]+)\}/g, (token, name) => {
      let replacement = token
      if (Object.prototype.hasOwnProperty.call(params, name) === true) {
        replacement = String(params[name])
      }
      return replacement
    })
  }
  return result
}

/*
 * Pick the plural form of `forms` for `params.count` in the current locale.
 * A missing category falls back to "other"; a missing count counts as 0.
 */
function selectPluralForm(forms, params) {
  let count = 0
  if (params !== null && params !== undefined && params.count !== undefined) {
    count = Number(params.count)
  }

  let category = "other"
  try {
    category = new Intl.PluralRules(currentLocale).select(count)
  } catch (error) {
    category = "other"
  }

  let form = forms[category]
  if (form === undefined) {
    form = forms.other
  }
  if (form === undefined) {
    form = ""
  }
  return String(form)
}

/*
 * Register or override localized strings. A value may be a string or a
 * plural object as described above STRINGS. Connected components render
 * again with the new strings.
 */
export function registerStrings(table) {
  const keys = Object.keys(table)
  for (let index = 0; index < keys.length; index = index + 1) {
    const key = keys[index]
    overrides[key] = table[key]
  }
  if (keys.length > 0) {
    notifyLocaleChange()
  }
  return
}

export function formatNumber(value, options) {
  const formatter = new Intl.NumberFormat(currentLocale, options || {})
  const formatted = formatter.format(value)
  return formatted
}

export function formatCurrency(value, currency) {
  const formatter = new Intl.NumberFormat(currentLocale, {
    style: "currency",
    currency: currency || "USD"
  })
  const formatted = formatter.format(value)
  return formatted
}

export function formatDate(value, options) {
  const date = value instanceof Date ? value : new Date(value)
  const formatter = new Intl.DateTimeFormat(currentLocale, options || { dateStyle: "medium" })
  const formatted = formatter.format(date)
  return formatted
}

export function formatRelativeTime(value, unit) {
  const formatter = new Intl.RelativeTimeFormat(currentLocale, { numeric: "auto" })
  const formatted = formatter.format(value, unit || "day")
  return formatted
}
