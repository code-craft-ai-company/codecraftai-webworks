# Web Component Specifications

Detailed specifications for the `automojo-webworks` web component library. Each
file specifies one **Primary** component (synonyms from the catalog are covered
by variants/modes within the relevant primary).

- Strategy, universal requirements, foundations, phasing: `../../web-component-development-plan.md`
- Per-component spec template: `_template.md`
- Component scripts will live at `source/packages/automojo/webworks/static/javascript/components`
- Component styles will live at `source/packages/automojo/webworks/static/styles`

Every spec follows `_template.md`: a header block plus 20 numbered sections
(purpose, anatomy, variants, attributes, properties, slots, events, CSS parts,
states, behavior, keyboard, accessibility, form participation, i18n/RTL, SSR,
dependencies, edge cases, acceptance criteria, open questions). The universal
requirements in plan §3 are referenced, not repeated, by each spec.

**138 component specs.**

## Selection & dropdown-style controls
- [select.md](select.md) — `<mj-select>`
- [listbox.md](listbox.md) — `<mj-listbox>`
- [combobox.md](combobox.md) — `<mj-combobox>`
- [cascadingselect.md](cascadingselect.md) — `<mj-cascading-select>`
- [radiogroup.md](radiogroup.md) — `<mj-radio-group>`
- [checkboxgroup.md](checkboxgroup.md) — `<mj-checkbox-group>`
- [segmentedcontrol.md](segmentedcontrol.md) — `<mj-segmented-control>`
- [splitbutton.md](splitbutton.md) — `<mj-split-button>`
- [menubutton.md](menubutton.md) — `<mj-menu-button>`
- [colorpicker.md](colorpicker.md) — `<mj-color-picker>`
- [datepicker.md](datepicker.md) — `<mj-date-picker>`
- [filepicker.md](filepicker.md) — `<mj-file-picker>`
- [assetpicker.md](assetpicker.md) — `<mj-asset-picker>`
- [localepicker.md](localepicker.md) — `<mj-locale-picker>`
- [tagpicker.md](tagpicker.md) — `<mj-tag-picker>`
- [treeselector.md](treeselector.md) — `<mj-tree-selector>`
- [transferlist.md](transferlist.md) — `<mj-transfer-list>`

## Text & data-entry controls
- [textfield.md](textfield.md) — `<mj-text-field>`
- [searchinput.md](searchinput.md) — `<mj-search-input>`
- [passwordfield.md](passwordfield.md) — `<mj-password-field>`
- [typedtextfield.md](typedtextfield.md) — `<mj-typed-field>`
- [numberfield.md](numberfield.md) — `<mj-number-field>`
- [textarea.md](textarea.md) — `<mj-textarea>`
- [richtexteditor.md](richtexteditor.md) — `<mj-rich-text-editor>`
- [markdowneditor.md](markdowneditor.md) — `<mj-markdown-editor>`
- [codeeditor.md](codeeditor.md) — `<mj-code-editor>`
- [inlineeditabletext.md](inlineeditabletext.md) — `<mj-inline-edit>`
- [maskedinput.md](maskedinput.md) — `<mj-masked-input>`
- [tokeninput.md](tokeninput.md) — `<mj-token-input>`
- [otpinput.md](otpinput.md) — `<mj-otp-input>`
- [slider.md](slider.md) — `<mj-slider>`
- [ratinginput.md](ratinginput.md) — `<mj-rating>`
- [captcha.md](captcha.md) — `<mj-captcha>`

### Form-structure primitives
- [form.md](form.md) — `<mj-form>`
- [fieldset.md](fieldset.md) — `<mj-fieldset>`
- [label.md](label.md) — `<mj-label>`
- [helptext.md](helptext.md) — `<mj-help-text>`
- [errormessage.md](errormessage.md) — `<mj-error-message>`
- [validationsummary.md](validationsummary.md) — `<mj-validation-summary>`
- [charactercounter.md](charactercounter.md) — `<mj-character-counter>`

## Buttons & actions
- [button.md](button.md) — `<mj-button>`
- [floatingactionbutton.md](floatingactionbutton.md) — `<mj-fab>`
- [togglebutton.md](togglebutton.md) — `<mj-toggle-button>`
- [disclosurebutton.md](disclosurebutton.md) — `<mj-disclosure-button>`
- [copybutton.md](copybutton.md) — `<mj-copy-button>`
- [sharebutton.md](sharebutton.md) — `<mj-share-button>`
- [favoritebutton.md](favoritebutton.md) — `<mj-favorite-button>`

## Navigation components
- [link.md](link.md) — `<mj-link>`
- [appbar.md](appbar.md) — `<mj-app-bar>`
- [sidenav.md](sidenav.md) — `<mj-side-nav>`
- [breadcrumb.md](breadcrumb.md) — `<mj-breadcrumb>`
- [tabs.md](tabs.md) — `<mj-tabs>`
- [navstepper.md](navstepper.md) — `<mj-nav-stepper>`
- [wizard.md](wizard.md) — `<mj-wizard>`
- [pagination.md](pagination.md) — `<mj-pagination>`
- [tableofcontents.md](tableofcontents.md) — `<mj-toc>`
- [skiplink.md](skiplink.md) — `<mj-skip-link>`
- [footernav.md](footernav.md) — `<mj-footer-nav>`
- [menu.md](menu.md) — `<mj-menu>`
- [treenavigation.md](treenavigation.md) — `<mj-tree-nav>`

## Layout & content containers
- [card.md](card.md) — `<mj-card>`
- [surface.md](surface.md) — `<mj-surface>`
- [grid.md](grid.md) — `<mj-grid>`
- [stack.md](stack.md) — `<mj-stack>`
- [spacer.md](spacer.md) — `<mj-spacer>`
- [aspectratiobox.md](aspectratiobox.md) — `<mj-aspect-ratio>`
- [accordion.md](accordion.md) — `<mj-accordion>`
- [disclosure.md](disclosure.md) — `<mj-disclosure>`
- [splitpane.md](splitpane.md) — `<mj-split-pane>`
- [scrollarea.md](scrollarea.md) — `<mj-scroll-area>`
- [carousel.md](carousel.md) — `<mj-carousel>`
- [feed.md](feed.md) — `<mj-feed>`
- [mediaobject.md](mediaobject.md) — `<mj-media-object>`
- [herosection.md](herosection.md) — `<mj-hero>`
- [emptystate.md](emptystate.md) — `<mj-empty-state>`
- [skeletonloader.md](skeletonloader.md) — `<mj-skeleton>`
- [divider.md](divider.md) — `<mj-divider>`

## Feedback & status components
- [alert.md](alert.md) — `<mj-alert>`
- [toast.md](toast.md) — `<mj-toast>`
- [progress.md](progress.md) — `<mj-progress>`
- [badge.md](badge.md) — `<mj-badge>`
- [chip.md](chip.md) — `<mj-chip>`
- [tooltip.md](tooltip.md) — `<mj-tooltip>`

## Dialogs, overlays & popups
- [dialog.md](dialog.md) — `<mj-dialog>`
- [popover.md](popover.md) — `<mj-popover>`
- [drawer.md](drawer.md) — `<mj-drawer>`
- [lightbox.md](lightbox.md) — `<mj-lightbox>`
- [overlay.md](overlay.md) — `<mj-overlay>`
- [toastregion.md](toastregion.md) — `<mj-toast-region>`
- [notificationcenter.md](notificationcenter.md) — `<mj-notification-center>`
- [contextmenu.md](contextmenu.md) — `<mj-context-menu>`
- [commandpalette.md](commandpalette.md) — `<mj-command-palette>`
- [tour.md](tour.md) — `<mj-tour>`

## Tables, lists & structured data
- [table.md](table.md) — `<mj-table>`
- [datatable.md](datatable.md) — `<mj-data-table>`
- [treegrid.md](treegrid.md) — `<mj-tree-grid>`
- [list.md](list.md) — `<mj-list>`
- [virtualizedlist.md](virtualizedlist.md) — `<mj-virtual-list>`
- [kanbanboard.md](kanbanboard.md) — `<mj-kanban>`
- [calendargrid.md](calendargrid.md) — `<mj-calendar>`
- [masterdetailview.md](masterdetailview.md) — `<mj-master-detail>`
- [columnpicker.md](columnpicker.md) — `<mj-column-picker>`
- [bulkactionbar.md](bulkactionbar.md) — `<mj-bulk-action-bar>`

## Media & visualization
- [image.md](image.md) — `<mj-image>`
- [avatar.md](avatar.md) — `<mj-avatar>`
- [mediaplayer.md](mediaplayer.md) — `<mj-media-player>`
- [chart.md](chart.md) — `<mj-chart>`
- [map.md](map.md) — `<mj-map>`
- [gauge.md](gauge.md) — `<mj-gauge>`
- [sparkline.md](sparkline.md) — `<mj-sparkline>`
- [diagram.md](diagram.md) — `<mj-diagram>`

## Application & productivity components
- [toolbar.md](toolbar.md) — `<mj-toolbar>`
- [menubar.md](menubar.md) — `<mj-menubar>`
- [statusbar.md](statusbar.md) — `<mj-status-bar>`
- [appshell.md](appshell.md) — `<mj-app-shell>`
- [searchresults.md](searchresults.md) — `<mj-search-results>`
- [filterpanel.md](filterpanel.md) — `<mj-filter-panel>`
- [querybuilder.md](querybuilder.md) — `<mj-query-builder>`
- [dropzone.md](dropzone.md) — `<mj-dropzone>`
- [filebrowser.md](filebrowser.md) — `<mj-file-browser>`
- [activityfeed.md](activityfeed.md) — `<mj-activity-feed>`
- [comments.md](comments.md) — `<mj-comments>`
- [mentioninput.md](mentioninput.md) — `<mj-mention-input>`
- [chatcomposer.md](chatcomposer.md) — `<mj-chat-composer>`
- [chatmessage.md](chatmessage.md) — `<mj-chat-message>`

## Project-management & configuration-management charts
- [branchgraph.md](branchgraph.md) — `<mj-branch-graph>`
- [pipelinechart.md](pipelinechart.md) — `<mj-pipeline-chart>`
- [ganttchart.md](ganttchart.md) — `<mj-gantt-chart>`
- [roadmapchart.md](roadmapchart.md) — `<mj-roadmap-chart>`
- [milestonetimeline.md](milestonetimeline.md) — `<mj-milestone-timeline>`
- [burndownchart.md](burndownchart.md) — `<mj-burndown-chart>`
- [cumulativeflowdiagram.md](cumulativeflowdiagram.md) — `<mj-cumulative-flow>`
- [velocitychart.md](velocitychart.md) — `<mj-velocity-chart>`
- [dependencygraph.md](dependencygraph.md) — `<mj-dependency-graph>`
- [workflowdiagram.md](workflowdiagram.md) — `<mj-workflow-diagram>`
- [releasecalendar.md](releasecalendar.md) — `<mj-release-calendar>`
- [environmentpromotionchart.md](environmentpromotionchart.md) — `<mj-env-promotion-chart>`
- [buildstatusboard.md](buildstatusboard.md) — `<mj-build-status-board>`
