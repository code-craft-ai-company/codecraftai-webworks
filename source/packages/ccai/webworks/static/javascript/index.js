/*
 * index.js
 *
 * Single entry point for the codecraftai-webworks (mj-*) web component library.
 * Importing this module imports every component and registers all custom
 * elements through the idempotent registry. Components themselves never call
 * customElements.define -- registration is centralized here.
 *
 *   <script type="module" src="/static/javascript/index.js"></script>
 *
 * The design tokens must also be linked so the palette inherits into every
 * component shadow root:
 *
 *   <link rel="stylesheet" href="/static/styles/tokens.css">
 *
 * Individual components remain independently importable for tree-shaking; this
 * barrel is the convenience "load everything" path.
 */

import { defineAll } from "./core/registry.js";

import { MjAccordion } from "./components/mjaccordion.js";
import { MjActivityFeed } from "./components/mjactivityfeed.js";
import { MjAlert } from "./components/mjalert.js";
import { MjAppBar } from "./components/mjappbar.js";
import { MjAppShell } from "./components/mjappshell.js";
import { MjAspectRatio } from "./components/mjaspectratio.js";
import { MjAssetPicker } from "./components/mjassetpicker.js";
import { MjAvatar } from "./components/mjavatar.js";
import { MjBadge } from "./components/mjbadge.js";
import { MjBranchGraph } from "./components/mjbranchgraph.js";
import { MjBreadcrumb } from "./components/mjbreadcrumb.js";
import { MjBuildStatusBoard } from "./components/mjbuildstatusboard.js";
import { MjBulkActionBar } from "./components/mjbulkactionbar.js";
import { MjBurndownChart } from "./components/mjburndownchart.js";
import { MjButton } from "./components/mjbutton.js";
import { MjCalendar } from "./components/mjcalendar.js";
import { MjCaptcha } from "./components/mjcaptcha.js";
import { MjCard } from "./components/mjcard.js";
import { MjCarousel } from "./components/mjcarousel.js";
import { MjCascadingSelect } from "./components/mjcascadingselect.js";
import { MjCharacterCounter } from "./components/mjcharactercounter.js";
import { MjChatComposer } from "./components/mjchatcomposer.js";
import { MjChatMessage } from "./components/mjchatmessage.js";
import { MjCheckboxGroup } from "./components/mjcheckboxgroup.js";
import { MjChip } from "./components/mjchip.js";
import { MjCodeEditor } from "./components/mjcodeeditor.js";
import { MjColorPicker } from "./components/mjcolorpicker.js";
import { MjColumnPicker } from "./components/mjcolumnpicker.js";
import { MjCombobox } from "./components/mjcombobox.js";
import { MjCommandPalette } from "./components/mjcommandpalette.js";
import { MjComments } from "./components/mjcomments.js";
import { MjContextMenu } from "./components/mjcontextmenu.js";
import { MjCopyButton } from "./components/mjcopybutton.js";
import { MjCumulativeFlow } from "./components/mjcumulativeflow.js";
import { MjDataTable } from "./components/mjdatatable.js";
import { MjDatePicker } from "./components/mjdatepicker.js";
import { MjDependencyGraph } from "./components/mjdependencygraph.js";
import { MjDiagram } from "./components/mjdiagram.js";
import { MjDialog } from "./components/mjdialog.js";
import { MjDisclosure } from "./components/mjdisclosure.js";
import { MjDisclosureButton } from "./components/mjdisclosurebutton.js";
import { MjDivider } from "./components/mjdivider.js";
import { MjDockLayout } from "./components/mjdocklayout.js";
import { MjDownloadButton } from "./components/mjdownloadbutton.js";
import { MjDrawer } from "./components/mjdrawer.js";
import { MjDropzone } from "./components/mjdropzone.js";
import { MjEmptyState } from "./components/mjemptystate.js";
import { MjEnvPromotionChart } from "./components/mjenvpromotionchart.js";
import { MjErrorMessage } from "./components/mjerrormessage.js";
import { MjFab } from "./components/mjfab.js";
import { MjFavoriteButton } from "./components/mjfavoritebutton.js";
import { MjFeed } from "./components/mjfeed.js";
import { MjFieldset } from "./components/mjfieldset.js";
import { MjFileBrowser } from "./components/mjfilebrowser.js";
import { MjFilePicker } from "./components/mjfilepicker.js";
import { MjFilterPanel } from "./components/mjfilterpanel.js";
import { MjFooterNav } from "./components/mjfooternav.js";
import { MjForm } from "./components/mjform.js";
import { MjGanttChart } from "./components/mjganttchart.js";
import { MjGauge } from "./components/mjgauge.js";
import { MjGrid } from "./components/mjgrid.js";
import { MjHelpText } from "./components/mjhelptext.js";
import { MjHero } from "./components/mjhero.js";
import { MjImage } from "./components/mjimage.js";
import { MjInlineEdit } from "./components/mjinlineedit.js";
import { MjKanban } from "./components/mjkanban.js";
import { MjLabel } from "./components/mjlabel.js";
import { MjLightbox } from "./components/mjlightbox.js";
import { MjLink } from "./components/mjlink.js";
import { MjList } from "./components/mjlist.js";
import { MjListbox } from "./components/mjlistbox.js";
import { MjLocalePicker } from "./components/mjlocalepicker.js";
import { MjMap } from "./components/mjmap.js";
import { MjMarkdownEditor } from "./components/mjmarkdowneditor.js";
import { MjMaskedInput } from "./components/mjmaskedinput.js";
import { MjMasterDetail } from "./components/mjmasterdetail.js";
import { MjMediaObject } from "./components/mjmediaobject.js";
import { MjMediaPlayer } from "./components/mjmediaplayer.js";
import { MjMentionInput } from "./components/mjmentioninput.js";
import { MjMenu } from "./components/mjmenu.js";
import { MjMenubar } from "./components/mjmenubar.js";
import { MjMenuButton } from "./components/mjmenubutton.js";
import { MjMilestoneTimeline } from "./components/mjmilestonetimeline.js";
import { MjNavStepper } from "./components/mjnavstepper.js";
import { MjNotificationCenter } from "./components/mjnotificationcenter.js";
import { MjNumberField } from "./components/mjnumberfield.js";
import { MjOtpInput } from "./components/mjotpinput.js";
import { MjOverlay } from "./components/mjoverlay.js";
import { MjPagination } from "./components/mjpagination.js";
import { MjPasswordField } from "./components/mjpasswordfield.js";
import { MjPipelineChart } from "./components/mjpipelinechart.js";
import { MjPopover } from "./components/mjpopover.js";
import { MjProgress } from "./components/mjprogress.js";
import { MjQueryBuilder } from "./components/mjquerybuilder.js";
import { MjRadioGroup } from "./components/mjradiogroup.js";
import { MjRating } from "./components/mjrating.js";
import { MjReleaseCalendar } from "./components/mjreleasecalendar.js";
import { MjRichTextEditor } from "./components/mjrichtexteditor.js";
import { MjRoadmapChart } from "./components/mjroadmapchart.js";
import { MjRowSelector } from "./components/mjrowselector.js";
import { MjScrollArea } from "./components/mjscrollarea.js";
import { MjSearchInput } from "./components/mjsearchinput.js";
import { MjSearchResults } from "./components/mjsearchresults.js";
import { MjSegmentedControl } from "./components/mjsegmentedcontrol.js";
import { MjSelect } from "./components/mjselect.js";
import { MjShareButton } from "./components/mjsharebutton.js";
import { MjSideNav } from "./components/mjsidenav.js";
import { MjSkeleton } from "./components/mjskeleton.js";
import { MjSkipLink } from "./components/mjskiplink.js";
import { MjSlider } from "./components/mjslider.js";
import { MjSortControl } from "./components/mjsortcontrol.js";
import { MjSpacer } from "./components/mjspacer.js";
import { MjSparkline } from "./components/mjsparkline.js";
import { MjSplitButton } from "./components/mjsplitbutton.js";
import { MjSplitPane } from "./components/mjsplitpane.js";
import { MjStack } from "./components/mjstack.js";
import { MjStatusBar } from "./components/mjstatusbar.js";
import { MjSurface } from "./components/mjsurface.js";
import { MjTable } from "./components/mjtable.js";
import { MjTabs } from "./components/mjtabs.js";
import { MjTagPicker } from "./components/mjtagpicker.js";
import { MjTextarea } from "./components/mjtextarea.js";
import { MjTextField } from "./components/mjtextfield.js";
import { MjToast } from "./components/mjtoast.js";
import { MjToastRegion } from "./components/mjtoastregion.js";
import { MjToc } from "./components/mjtoc.js";
import { MjToggleButton } from "./components/mjtogglebutton.js";
import { MjTokenInput } from "./components/mjtokeninput.js";
import { MjToolbar } from "./components/mjtoolbar.js";
import { MjTooltip } from "./components/mjtooltip.js";
import { MjTour } from "./components/mjtour.js";
import { MjTransferList } from "./components/mjtransferlist.js";
import { MjTreeGrid } from "./components/mjtreegrid.js";
import { MjTreeNav } from "./components/mjtreenav.js";
import { MjTreeSelector } from "./components/mjtreeselector.js";
import { MjTypedField } from "./components/mjtypedfield.js";
import { MjUploadButton } from "./components/mjuploadbutton.js";
import { MjValidationSummary } from "./components/mjvalidationsummary.js";
import { MjVelocityChart } from "./components/mjvelocitychart.js";
import { MjVirtualList } from "./components/mjvirtuallist.js";
import { MjWizard } from "./components/mjwizard.js";
import { MjWorkflowDiagram } from "./components/mjworkflowdiagram.js";

/* The complete component set, in registration order. */
export const components = [
  MjAccordion, MjActivityFeed, MjAlert, MjAppBar, MjAppShell, MjAspectRatio,
  MjAssetPicker, MjAvatar, MjBadge, MjBranchGraph, MjBreadcrumb,
  MjBuildStatusBoard, MjBulkActionBar, MjBurndownChart, MjButton, MjCalendar,
  MjCaptcha, MjCard, MjCarousel, MjCascadingSelect, MjCharacterCounter,
  MjChatComposer, MjChatMessage, MjCheckboxGroup, MjChip,
  MjCodeEditor, MjColorPicker, MjColumnPicker, MjCombobox, MjCommandPalette,
  MjComments, MjContextMenu, MjCopyButton, MjCumulativeFlow, MjDataTable,
  MjDatePicker, MjDependencyGraph, MjDiagram, MjDialog, MjDisclosure,
  MjDisclosureButton, MjDivider, MjDockLayout, MjDownloadButton, MjDrawer,
  MjDropzone,
  MjEmptyState, MjEnvPromotionChart, MjErrorMessage, MjFab, MjFavoriteButton,
  MjFeed, MjFieldset, MjFileBrowser, MjFilePicker, MjFilterPanel, MjFooterNav,
  MjForm, MjGanttChart, MjGauge, MjGrid, MjHelpText, MjHero, MjImage,
  MjInlineEdit, MjKanban, MjLabel, MjLightbox, MjLink, MjList, MjListbox,
  MjLocalePicker, MjMap, MjMarkdownEditor, MjMaskedInput, MjMasterDetail,
  MjMediaObject, MjMediaPlayer, MjMentionInput, MjMenu, MjMenubar,
  MjMenuButton, MjMilestoneTimeline, MjNavStepper, MjNotificationCenter,
  MjNumberField, MjOtpInput, MjOverlay, MjPagination, MjPasswordField,
  MjPipelineChart, MjPopover, MjProgress, MjQueryBuilder, MjRadioGroup,
  MjRating, MjReleaseCalendar, MjRichTextEditor, MjRoadmapChart, MjRowSelector,
  MjScrollArea, MjSearchInput, MjSearchResults, MjSegmentedControl, MjSelect,
  MjShareButton, MjSideNav, MjSkeleton, MjSkipLink, MjSlider, MjSortControl,
  MjSpacer, MjSparkline,
  MjSplitButton, MjSplitPane, MjStack, MjStatusBar, MjSurface, MjTable,
  MjTabs, MjTagPicker, MjTextarea, MjTextField, MjToast, MjToastRegion,
  MjToc, MjToggleButton, MjTokenInput, MjToolbar, MjTooltip, MjTour,
  MjTransferList, MjTreeGrid, MjTreeNav, MjTreeSelector, MjTypedField,
  MjUploadButton, MjValidationSummary, MjVelocityChart, MjVirtualList,
  MjWizard, MjWorkflowDiagram
];

/* Register every component. Safe to import more than once (idempotent). */
export const registeredTags = defineAll(components);

/* The chart library: <mj-chart> controller, parts, and all renderers.
 * Importing it registers <mj-chart> and the coordinated chart parts. */
import "./charts/index.js";

export * from "./core/registry.js";
export { setLocale, getLocale, t, registerStrings } from "./core/intl.js";
export { announce } from "./core/announcer.js";
