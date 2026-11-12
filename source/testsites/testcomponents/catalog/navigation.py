"""
    navigation.py

    Catalog entries for the 'Navigation' component group.

    Every navigation component exposed by the mj-* library is described here
    as a ComponentDoc instance.  The module-level ``COMPONENTS`` list is
    consumed by the testcomponents site to build the live component catalog.

    The preview is an ``srcdoc`` frame: a link -- even a ``#fragment`` link --
    resolves against the catalog page and would load that page into the
    preview. Every example with links therefore cancels link navigation in its
    script (``_LINK_GUARD``) and logs it instead, after the component has had
    its say (its own cancelable navigate event still fires first).
"""

import textwrap

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.componentdoc import ComponentExample


def _block(text: str) -> str:
    """
        Dedent an indented triple-quoted block and strip the surrounding blank
        lines, so example markup can be written indented in this module.

        :param text: The indented text.

        :returns: The dedented text.
    """

    rtnval = textwrap.dedent(text).strip("\n") + "\n"
    return rtnval


# Cancels link navigation in the preview (see the module docstring) and logs it.
_LINK_GUARD = _block("""
    // The preview is an srcdoc frame: following any link (even "#...") would load
    // another page into it, so link activations are logged instead of followed.
    document.addEventListener("click", (event) => {
      const link = event.composedPath().find((node) => node instanceof Element && node.matches("a[href]"))
      if (link !== undefined && event.defaultPrevented === false) {
        event.preventDefault()
        mjSandbox.log("link activated (navigation suppressed)", { href: link.getAttribute("href") })
      }
    })
""")

_BTN_CSS = _block("""
    .btn { min-block-size: var(--mj-control-height-md); padding-inline: var(--mj-space-4); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-md); background: var(--mj-surface); color: var(--mj-text); font: inherit; cursor: pointer; }
""")

_SEARCH_ICON = (
    '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" fill="none" '
    'stroke="currentColor" stroke-width="1.5"><circle cx="7" cy="7" r="4.5"/>'
    '<line x1="10.5" y1="10.5" x2="14" y2="14" stroke-linecap="round"/></svg>'
)

_DOWNLOAD_ICON = (
    '<svg slot="prefix" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M8 2v8M4.5 6.5 8 10l3.5-3.5M3 13h10"/></svg>'
)

_FILLER = (
    "Each section holds enough text to scroll, so the active link follows the "
    "heading that has passed the top part of the frame. Scroll this panel or "
    "click a link in the table of contents."
)


# ---------------------------------------------------------------------------
# mj-link
# ---------------------------------------------------------------------------

_LINK = ComponentDoc(
    tag="mj-link",
    title="Link",
    group="navigation",
    summary="A styled hyperlink built on a real &lt;a&gt;, with variants, safe external links and a disabled state.",
    description=(
        "<p><code>&lt;mj-link&gt;</code> renders a native <code>&lt;a&gt;</code> in its shadow root and "
        "copies <code>href</code>, <code>target</code>, <code>rel</code> and <code>download</code> onto it "
        "(attribute values are never parsed as markup; a <code>javascript:</code> URL becomes "
        "<code>#</code>). Without <code>href</code> the anchor has none, so it is not a link to the current "
        "page.</p>"
        "<p><code>external</code> opens the link in a new tab, adds <code>noopener noreferrer</code>, an "
        "external-link icon and the hidden text &ldquo;opens in a new tab&rdquo;. Any "
        "<code>target=\"_blank\"</code> gets <code>noopener</code> as well.</p>"
        "<p>A <code>disabled</code> link loses its <code>href</code> but keeps <code>role=\"link\"</code>, "
        "<code>tabindex=\"0\"</code> and <code>aria-disabled=\"true\"</code>: it stays in the tab order and "
        "is announced as an unavailable link; clicks are swallowed and no event fires.</p>"
    ),
    how_to_use=(
        "<p>Set <code>href</code> and put the link text between the tags. Pick a <code>variant</code>: "
        "none (underlined, for prose), <code>subtle</code> (underline on hover and focus) or "
        "<code>standalone</code> (block, medium weight, touch-target height, for calls to action). Add an "
        "icon with the <code>prefix</code> slot. Add <code>external</code> for links that leave the site and "
        "<code>visited-cue</code> where a visited colour helps (long link lists).</p>"
        "<p>Every activation emits the cancelable <code>mj-link-click</code> with "
        "<code>{ href, external, originalEvent }</code>; call <code>preventDefault()</code> to handle the "
        "navigation yourself (client-side routing). The examples cancel navigation because the preview "
        "cannot leave its page.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="href", description="Destination URL, copied to the inner anchor. Absent: the anchor has no href.",
                     kind="string", values=["#pricing", "/docs/", "https://www.example.org/"]),
        AttributeDoc(name="variant", description="Visual style. `default` (or absent) is the underlined prose link.",
                     kind="enum", values=["default", "subtle", "standalone"], default="default"),
        AttributeDoc(name="external", description="Opens in a new tab (target `_blank` unless `target` is set), adds `noopener noreferrer`, the icon and a hidden \"opens in a new tab\". Present = on.",
                     kind="boolean"),
        AttributeDoc(name="target", description="Browsing context for the anchor; `_blank` also adds `noopener`.",
                     kind="string", values=["_self", "_blank", "_parent", "_top"]),
        AttributeDoc(name="rel", description="Link relations; `noopener` (and `noreferrer` for external) are appended when needed.",
                     kind="string", values=["nofollow", "noopener", "noreferrer", "help"]),
        AttributeDoc(name="download", description="Downloads the target instead of navigating; the value is the suggested file name.",
                     kind="string", values=["report.pdf"]),
        AttributeDoc(name="disabled", description="Removes the href, keeps role link and tabindex 0, sets aria-disabled and blocks clicks.",
                     kind="boolean"),
        AttributeDoc(name="visited-cue", description="Shows visited links in `--mj-link-color-visited`. `visited-cue=\"false\"` turns it off.",
                     kind="boolean"),
    ],
    events=[
        ("mj-link-click", "Cancelable; fired on activation of an enabled link. Canceling prevents the navigation.",
         "{ href: string, external: boolean, originalEvent: MouseEvent }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>Links in running text. Clicking one logs <code>mj-link-click</code>; the preview suppresses the navigation.</p>",
            html=_block("""
                <p>
                  Compare plans on the <mj-link id="demo-link" href="#pricing">pricing page</mj-link>
                  or read the <mj-link href="#docs/getting-started">getting-started guide</mj-link>
                  before you invite your team.
                </p>
            """),
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="variants",
            title="Variants",
            description="<p><code>standalone</code> for calls to action, the default underlined link for prose and <code>subtle</code>, which underlines only on hover and focus.</p>",
            html=_block("""
                <div class="stack">
                  <mj-link href="#account" variant="standalone">Manage your account</mj-link>
                  <p>Default: read the <mj-link href="#terms">terms of service</mj-link>.</p>
                  <p>Subtle: see our <mj-link href="#privacy" variant="subtle">privacy notice</mj-link>.</p>
                </div>
            """),
            css=".stack { display: grid; gap: var(--mj-space-3); }\n.stack p { margin: 0; }\n",
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="with-icons",
            title="Icon and external",
            description="<p>A leading icon in the <code>prefix</code> slot, and an <code>external</code> link with its icon and new-tab semantics (inspect the inner anchor's <code>target</code> and <code>rel</code>).</p>",
            html=_block("""
                <div class="stack">
                  <mj-link href="#downloads/annual-report" variant="standalone">
                    """ + _DOWNLOAD_ICON + """
                    Annual report 2026
                  </mj-link>
                  <p>Service health is on the <mj-link href="https://status.example.org/" external>status page</mj-link>.</p>
                  <p><mj-link href="#help" target="_blank">Help centre in a new tab</mj-link> (target only: gets <code>noopener</code>).</p>
                </div>
            """),
            css=".stack { display: grid; gap: var(--mj-space-3); }\n.stack p { margin: 0; }\n",
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="states",
            title="Disabled, visited, download",
            description="<p>A disabled link stays focusable (press Tab) but cannot be activated; <code>visited-cue</code> mutes a visited link (this page is visited); <code>download</code> asks for a file.</p>",
            html=_block("""
                <ul class="stack">
                  <li><mj-link id="billing-link" href="#billing" disabled>Billing (requires the admin role)</mj-link></li>
                  <li><mj-link href="/components/navigation/mj-link" visited-cue>This catalog page (already visited)</mj-link></li>
                  <li><mj-link href="/static/styles/tokens.css" download="tokens.css">Download tokens.css</mj-link></li>
                </ul>
            """),
            css=".stack { display: grid; gap: var(--mj-space-3); margin: 0; padding-inline-start: var(--mj-space-5); }\n",
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="events",
            title="Client-side routing",
            description="<p>The script cancels <code>mj-link-click</code> and switches the view itself, like a client-side router. Watch the Events panel and the current view.</p>",
            html=_block("""
                <nav class="routes" aria-label="Sections">
                  <mj-link id="route-home" href="#/home" variant="subtle">Home</mj-link>
                  <mj-link href="#/reports" variant="subtle">Reports</mj-link>
                  <mj-link href="#/settings" variant="subtle">Settings</mj-link>
                </nav>
                <p>Current view: <output id="route-view">home</output></p>
            """),
            css=".routes { display: flex; gap: var(--mj-space-4); }\n",
            script=_block("""
                const view = document.getElementById("route-view")
                for (const link of document.querySelectorAll(".routes mj-link")) {
                  link.addEventListener("mj-link-click", (event) => {
                    event.preventDefault()
                    view.textContent = event.detail.href.replace("#/", "")
                    mjSandbox.log("routed client-side", { href: event.detail.href })
                  })
                }
            """),
        ),
    ],
    slots=[
        ("", "Link text.", "Read the guide"),
        ("prefix", "Leading icon or badge, before the text.",
         '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><circle cx="8" cy="8" r="5" fill="currentColor"/></svg>'),
    ],
    properties=[
        ("anchorElement", "HTMLAnchorElement | null. The inner anchor (read-only)."),
        ("disabled", "boolean. Reflects the `disabled` attribute."),
    ],
    parts=[
        ("anchor", "The inner native anchor."),
        ("prefix", "Wrapper of the `prefix` slot."),
        ("external-icon", "The external-link icon (shown with `external`)."),
    ],
    css_properties=[
        ("--mj-link-color", "Link colour (default var(--mj-accent))."),
        ("--mj-link-color-hover", "Hover colour (default var(--mj-accent-hover))."),
        ("--mj-link-color-visited", "Visited colour with `visited-cue` (default var(--mj-text-muted))."),
        ("--mj-link-color-disabled", "Disabled colour (default var(--mj-text-muted))."),
        ("--mj-link-underline-offset", "Underline offset (default 2px)."),
        ("--mj-link-external-icon-size", "Size of the external icon (default 0.875em)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-app-bar
# ---------------------------------------------------------------------------

_APP_BAR_CSS = _block("""
    mj-app-bar a { color: var(--mj-text); text-decoration: none; }
    mj-app-bar a:hover { text-decoration: underline; }
    mj-app-bar a[aria-current="page"] { color: var(--mj-accent); font-weight: var(--mj-font-weight-medium); }
    mj-app-bar .brand { font-weight: var(--mj-font-weight-bold, 700); }
    mj-app-bar .icon-btn, mj-app-bar .text-btn {
      display: inline-flex; align-items: center; justify-content: center;
      min-block-size: var(--mj-control-height-sm); padding-inline: var(--mj-space-3);
      border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md);
      background: var(--mj-surface); color: var(--mj-text); font: inherit; cursor: pointer;
    }
    mj-app-bar .icon-btn { padding-inline: var(--mj-space-2); }
""")

_APP_BAR = ComponentDoc(
    tag="mj-app-bar",
    title="App Bar",
    group="navigation",
    summary="Top-of-page bar with brand, navigation and actions that collapses into a modal drawer on narrow viewports.",
    description=(
        "<p><code>&lt;mj-app-bar&gt;</code> renders a <code>&lt;header&gt;</code> with three areas: "
        "<code>brand</code>, a <code>&lt;nav&gt;</code> holding the <code>navigation</code> slot, and "
        "<code>actions</code>. "
        "Below the collapse breakpoint (default 768px of viewport width, see "
        "<code>collapse-breakpoint</code>) the navigation is hidden and a menu button opens a slide-in drawer. "
        "The drawer shows the same <code>navigation</code> links (the slot is moved into it), or the "
        "<code>mobile-navigation</code> content when there is some. The open drawer is a modal dialog: focus "
        "is trapped, the page does not scroll, and Escape or a click on the backdrop closes it.</p>"
        "<p>Without anything in <code>navigation</code> or <code>mobile-navigation</code> the bar exposes no "
        "(empty) navigation landmark and no menu button.</p>"
        "<p>The header is the page's <code>banner</code> landmark. A page has one banner, so a bar is "
        "not the banner (its header gets <code>role=\"none\"</code>) when it sits inside a landmark, a "
        "section, an article or a dialog (including an <code>mj-app-shell</code> app-bar region the "
        "shell made the banner), when the page has a <code>&lt;header&gt;</code> banner of its own, or "
        "when another bar connected before it already is the banner.</p>"
        "<p><code>transparent</code> (or <code>variant=\"transparent\"</code>) starts with no background and "
        "no shadow; once the page, or the nearest scrolling container, has scrolled past "
        "<code>scroll-threshold</code> pixels the bar gets the read-only <code>scrolled</code> attribute and "
        "with it a background and shadow.</p>"
        "<p>Inside an <code>&lt;mj-app-shell&gt;</code> that has <code>nav</code> content, the shell owns the "
        "navigation: the menu button opens and closes the shell's nav (its <code>aria-expanded</code> follows "
        "<code>shell.navOpen</code>) and the bar's own drawer never opens. The bar's button stands in for the "
        "shell's own toggle: set <code>hide-nav-toggle</code> on the shell to use it. It is then shown wherever "
        "the shell's nav can be toggled (the shell is narrow, or its <code>nav-mode</code> is "
        "<code>overlay</code> or <code>collapsible</code>), whether or not the bar has navigation of its own; "
        "without <code>hide-nav-toggle</code> the shell's toggle is used and the bar shows none. The bar's "
        "<code>navigation</code> links stay in the bar at every width (scrolling sideways when they do not "
        "fit) and <code>collapse-breakpoint</code> does not apply.</p>"
    ),
    how_to_use=(
        "<p>Put the product name or logo in <code>brand</code>, links in <code>navigation</code> (mark the "
        "current one with <code>aria-current=\"page\"</code>) and buttons in <code>actions</code>. Add "
        "<code>sticky</code> to keep the bar at the top while the content scrolls. Use "
        "<code>mobile-navigation</code> only when the drawer should show different links.</p>"
        "<p>The cancelable <code>mj-app-bar-open</code> / <code>mj-app-bar-close</code> fire before the "
        "drawer changes (toggle, backdrop, Escape); <code>mj-app-bar-scroll</code> reports changes of the "
        "scrolled state. Setting <code>open</code> (attribute or property) emits nothing.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="sticky", description="Sticks the bar to the top of its scrolling container.", kind="boolean"),
        AttributeDoc(name="open", description="Opens the mobile drawer (visible only in the collapsed layout).", kind="boolean"),
        AttributeDoc(name="variant", description="`floating` (inset, rounded), `compact` (40px) or `transparent` (same as the `transparent` attribute).",
                     kind="enum", values=["floating", "compact", "transparent"]),
        AttributeDoc(name="compact", description="Compact height (40px), same as `variant=\"compact\"`.", kind="boolean"),
        AttributeDoc(name="transparent", description="No background or shadow until the content has scrolled past `scroll-threshold`.", kind="boolean"),
        AttributeDoc(name="scroll-threshold", description="Scroll distance in px before `scrolled` is set.", kind="number", default="16"),
        AttributeDoc(name="collapse-breakpoint", description="Viewport width below which the bar collapses into the drawer: `sm` (640), `md` (768), `lg` (1024) or a pixel number.",
                     kind="string", values=["sm", "md", "lg", "1200"], default="md"),
        AttributeDoc(name="nav-label", description="Accessible name of the navigation landmark and the drawer.", kind="string",
                     values=["Main", "Product"], default="Main"),
        AttributeDoc(name="scrolled", description="State set by the component when the content has scrolled past the threshold; do not set it.",
                     kind="boolean"),
    ],
    events=[
        ("mj-app-bar-open", "Cancelable; the menu button is about to open the drawer (or the enclosing shell's nav).", "{}"),
        ("mj-app-bar-close", "Cancelable; the drawer is about to close (menu button, backdrop click or Escape).", "{}"),
        ("mj-app-bar-scroll", "The scrolled state changed while scrolling.", "{ scrolled: boolean, scrollY: number }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>Brand, navigation and actions, above the page's <code>main</code> content: the bar is the page's banner landmark. Narrow the window below 768px to get the menu button and drawer.</p>",
            html=_block("""
                <mj-app-bar id="demo-bar" nav-label="Main">
                  <a slot="brand" class="brand" href="#home">Northwind</a>
                  <a slot="navigation" href="#dashboard" aria-current="page">Dashboard</a>
                  <a slot="navigation" href="#orders">Orders</a>
                  <a slot="navigation" href="#customers">Customers</a>
                  <a slot="navigation" href="#reports">Reports</a>
                  <button slot="actions" type="button" class="icon-btn" aria-label="Search">""" + _SEARCH_ICON + """</button>
                  <button slot="actions" type="button" class="text-btn">Sign in</button>
                </mj-app-bar>
                <main class="page"><p>Page content under the bar.</p></main>
            """),
            css=_APP_BAR_CSS + ".page { padding: var(--mj-space-4); }\n",
            script=_LINK_GUARD,
            height=360,
        ),
        ComponentExample(
            key="variants",
            title="Variants",
            description="<p><code>floating</code>, <code>compact</code>, and a bar without navigation, which has no navigation landmark and no menu button. The bars sit in the page's <code>main</code> content (a gallery), so none of them is the page banner.</p>",
            html=_block("""
                <main class="stack">
                  <mj-app-bar variant="floating" nav-label="Floating">
                    <a slot="brand" class="brand" href="#home">Northwind</a>
                    <a slot="navigation" href="#features">Features</a>
                    <a slot="navigation" href="#pricing">Pricing</a>
                    <button slot="actions" type="button" class="text-btn">Start trial</button>
                  </mj-app-bar>
                  <mj-app-bar compact nav-label="Compact">
                    <a slot="brand" class="brand" href="#home">Admin</a>
                    <a slot="navigation" href="#users" aria-current="page">Users</a>
                    <a slot="navigation" href="#audit">Audit log</a>
                  </mj-app-bar>
                  <mj-app-bar>
                    <span slot="brand" class="brand">Status</span>
                    <button slot="actions" type="button" class="text-btn">Subscribe to updates</button>
                  </mj-app-bar>
                </main>
            """),
            css=_APP_BAR_CSS + ".stack { display: grid; gap: var(--mj-space-4); }\n",
            script=_LINK_GUARD,
            height=360,
        ),
        ComponentExample(
            key="mobile-drawer",
            title="Mobile drawer",
            description="<p><code>collapse-breakpoint=\"4000\"</code> forces the collapsed layout. Open the drawer with the menu button: the <code>navigation</code> links move into it. Close with Escape, the backdrop or the button. Toggle <code>mobile-navigation</code> in Slots to give the drawer its own links.</p>",
            html=_block("""
                <mj-app-bar id="phone-bar" collapse-breakpoint="4000" nav-label="Main">
                  <a slot="brand" class="brand" href="#home">Northwind</a>
                  <a slot="navigation" href="#dashboard" aria-current="page">Dashboard</a>
                  <a slot="navigation" href="#orders">Orders</a>
                  <a slot="navigation" href="#customers">Customers</a>
                  <button slot="actions" type="button" class="icon-btn" aria-label="Search">""" + _SEARCH_ICON + """</button>
                </mj-app-bar>
                <main class="page"><p>Content under the bar.</p></main>
            """),
            css=_APP_BAR_CSS + ".page { padding: var(--mj-space-4); }\n",
            script=_LINK_GUARD,
            height=420,
        ),
        ComponentExample(
            key="events",
            title="Sticky and transparent",
            description="<p>A <code>sticky transparent</code> bar in a scrolling panel. The script scrolls the panel once: the bar gains <code>scrolled</code> (background and shadow) and <code>mj-app-bar-scroll</code> is logged. Scroll back up to see it turn transparent again.</p>",
            html=_block("""
                <div class="scroller" id="scroller">
                  <mj-app-bar id="scroll-bar" sticky transparent scroll-threshold="40" nav-label="Product">
                    <a slot="brand" class="brand" href="#home">Northwind</a>
                    <a slot="navigation" href="#tour">Tour</a>
                    <a slot="navigation" href="#pricing">Pricing</a>
                    <button slot="actions" type="button" class="text-btn">Sign in</button>
                  </mj-app-bar>
                  <main>
                    <section class="hero"><h2>Ship orders faster</h2><p>Scroll this panel.</p></section>
                    <p>Northwind keeps every order, invoice and shipment in one place.</p>
                    <p>Teams share one inbox per customer and see the full history of each order.</p>
                    <p>Reports update as orders move, so nobody waits for the end of the month.</p>
                    <p>Integrations sync stock levels with the warehouse twice a minute.</p>
                    <p>Exports produce spreadsheets your accountant already understands.</p>
                  </main>
                </div>
            """),
            css=_APP_BAR_CSS + _block("""
                .scroller { block-size: 300px; overflow: auto; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
                .scroller main > p { margin: var(--mj-space-5) var(--mj-space-5); }
                .hero { margin-block-start: -56px; padding: 96px var(--mj-space-5) var(--mj-space-8); background: var(--mj-bg-subtle); }
                .hero h2 { margin: 0 0 var(--mj-space-2); }
            """),
            script=_LINK_GUARD + _block("""
                const scroller = document.getElementById("scroller")
                const bar = document.getElementById("scroll-bar")
                bar.addEventListener("mj-app-bar-scroll", (event) => {
                  mjSandbox.log(event.detail.scrolled ? "bar is opaque" : "bar is transparent", event.detail)
                })
                setTimeout(() => { scroller.scrollTop = 160 }, 300)
            """),
        ),
        ComponentExample(
            key="in-app-shell",
            title="Inside mj-app-shell",
            description="<p>Inside an <code>mj-app-shell</code> with <code>nav</code> content the bar's menu button opens the shell's navigation (watch <code>aria-expanded</code> on the button follow <code>shell.navOpen</code>). It is shown because the shell's <code>nav-mode=\"overlay\"</code> can be toggled at any width; the bar's own links (Docs, Support) stay in the bar. <code>hide-nav-toggle</code> hands the toggle from the shell to the bar; remove it in the HTML pane and Run to get the shell's toggle instead.</p>",
            html=_block("""
                <mj-app-shell id="shell" nav-mode="overlay" hide-nav-toggle>
                  <mj-app-bar slot="app-bar" id="shell-bar" nav-label="Product">
                    <a slot="brand" class="brand" href="#home">Northwind</a>
                    <a slot="navigation" href="#docs">Docs</a>
                    <a slot="navigation" href="#support">Support</a>
                  </mj-app-bar>
                  <nav slot="nav" aria-label="Sections" class="shell-nav">
                    <a href="#dashboard">Dashboard</a>
                    <a href="#orders">Orders</a>
                    <a href="#customers">Customers</a>
                  </nav>
                  <p>Use the menu button in the bar to open the shell navigation.</p>
                </mj-app-shell>
            """),
            css=_APP_BAR_CSS + _block("""
                #shell { block-size: 400px; }
                .shell-nav { display: grid; gap: var(--mj-space-3); padding: var(--mj-space-4); }
                .shell-nav a { color: var(--mj-text); }
            """),
            script=_LINK_GUARD + _block("""
                const shell = document.getElementById("shell")
                shell.addEventListener("mj-shell-nav-toggle", () => mjSandbox.log("shell.navOpen", { navOpen: shell.navOpen }))
            """),
            height=420,
        ),
    ],
    slots=[
        ("brand", "Logo or product name at the inline start.", '<a href="#home" class="brand">Acme</a>'),
        ("navigation", "Navigation links; shown in the bar, and in the drawer when collapsed (unless `mobile-navigation` has content). Inside a shell that owns the navigation they always stay in the bar.",
         '<a href="#docs">Docs</a><a href="#blog">Blog</a>'),
        ("actions", "Buttons at the inline end (search, account).",
         '<button type="button" class="text-btn">Help</button>'),
        ("mobile-navigation", "Replaces the drawer content in the collapsed layout.",
         '<a href="#help">Help centre</a><a href="#sign-out">Sign out</a>'),
    ],
    properties=[
        ("open", "boolean. Reflects the `open` attribute; setting it emits no event."),
        ("scrolled", "boolean. True while the content is scrolled past the threshold (read-only)."),
        ("drawerElement", "HTMLElement | null. The drawer dialog in the shadow root (read-only)."),
    ],
    parts=[
        ("root", "The bar row: the `<header>` (the banner landmark, or `role=\"none\"` when the bar is not the page banner)."),
        ("brand", "Wrapper of the `brand` slot."),
        ("nav", "The navigation landmark in the bar."),
        ("actions", "Wrapper of the `actions` slot."),
        ("toggle", "The menu button (collapsed layout; inside a shell that owns the navigation and has `hide-nav-toggle`, wherever the shell's nav can be toggled)."),
        ("backdrop", "Scrim behind the open drawer."),
        ("drawer", "The drawer dialog."),
    ],
    css_properties=[
        ("--mj-app-bar-height", "Bar height (default 56px)."),
        ("--mj-app-bar-height-compact", "Compact bar height (default 40px)."),
        ("--mj-app-bar-padding-inline", "Inline padding (default var(--mj-space-5); var(--mj-space-4) when compact)."),
        ("--mj-app-bar-bg", "Background (default var(--mj-surface))."),
        ("--mj-app-bar-bg-scrolled", "Background of a transparent bar once scrolled (default var(--mj-surface))."),
        ("--mj-app-bar-elevation", "Shadow (default var(--mj-elevation-2); floating var(--mj-elevation-3))."),
        ("--mj-app-bar-z-index", "Stacking level (default var(--mj-layer-sticky))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-side-nav
# ---------------------------------------------------------------------------

_SIDE_NAV_LAYOUT_CSS = _block("""
    .layout { display: flex; block-size: 320px; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); overflow: hidden; }
    .layout mj-side-nav { border-inline-end: 1px solid var(--mj-border); }
    .content { flex: 1; padding: var(--mj-space-5); }
    .content h2 { margin-block-start: 0; }
""")

_SIDE_NAV = ComponentDoc(
    tag="mj-side-nav",
    title="Side Nav",
    group="navigation",
    summary="Side navigation landmark with static, collapsible (rail) and overlay-drawer modes.",
    description=(
        "<p><code>&lt;mj-side-nav&gt;</code> is a <code>&lt;nav&gt;</code> landmark with a "
        "<code>header</code>, the item list (default slot) and a <code>footer</code>. Items are the slotted "
        "links and buttons, and those nested in slotted wrappers (groups). They form one tab stop: "
        "ArrowUp / ArrowDown (wrapping), Home and End move between items; keys typed in header or footer "
        "content are left alone. The item with <code>aria-current=\"page\"</code> is highlighted and holds the "
        "tab stop.</p>"
        "<p>Modes: <code>static</code> (default, always shown); <code>collapsible</code>, which needs "
        "<code>open</code> to start expanded and collapses to a narrow rail that keeps its toggle button; and "
        "<code>overlay-drawer</code>, a modal panel over the page (opened with <code>show()</code> or "
        "<code>open</code>; while open, focus is trapped, the rest of the page is inert and does not scroll, and "
        "Escape or the backdrop closes it).</p>"
        "<p>In collapsible mode the open/closed state is saved in <code>localStorage</code> under "
        "<code>persist-key</code> and restored on the next load; <code>persist-state=\"false\"</code> turns "
        "that off.</p>"
    ),
    how_to_use=(
        "<p>Put links (or buttons) in the default slot and mark the current page with "
        "<code>aria-current=\"page\"</code>; style nested items yourself, since only direct children get the "
        "built-in item styles. Give the host a height (the panel fills it). For a drawer, call "
        "<code>show()</code> from your menu button and <code>hide()</code> from a close button.</p>"
        "<p><code>show()</code>, <code>hide()</code>, the collapsible toggle, Escape and the backdrop emit the "
        "cancelable <code>mj-side-nav-open</code> / <code>mj-side-nav-close</code> with "
        "<code>{ mode }</code>. Setting the <code>open</code> attribute or property emits nothing.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="mode", description="Layout mode.", kind="enum",
                     values=["static", "collapsible", "overlay-drawer"], default="static"),
        AttributeDoc(name="open", description="Expanded (collapsible) or shown (overlay-drawer). Ignored in static mode.", kind="boolean"),
        AttributeDoc(name="edge", description="Edge the overlay drawer slides in from.", kind="enum",
                     values=["start", "end"], default="start"),
        AttributeDoc(name="nav-label", description="Accessible name of the nav landmark.", kind="string",
                     values=["Workspace", "Site"], default="Navigation"),
        AttributeDoc(name="persist-state", description="Collapsible mode saves open/closed in localStorage; uncheck (`false`) to turn it off.",
                     kind="boolean", default="true"),
        AttributeDoc(name="persist-key", description="localStorage key for the saved state.", kind="string", default="mj-side-nav"),
    ],
    events=[
        ("mj-side-nav-open", "Cancelable; about to open (toggle button or `show()`).", "{ mode: 'static' | 'collapsible' | 'overlay-drawer' }"),
        ("mj-side-nav-close", "Cancelable; about to close (toggle, `hide()`, Escape or backdrop in overlay-drawer).", "{ mode: 'static' | 'collapsible' | 'overlay-drawer' }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>A static side nav with header, items and footer. Focus an item and use the arrow keys, Home and End.</p>",
            html=_block("""
                <div class="layout">
                  <mj-side-nav id="demo-side-nav" nav-label="Workspace">
                    <strong slot="header">Northwind</strong>
                    <a href="#dashboard" aria-current="page">Dashboard</a>
                    <a href="#orders">Orders</a>
                    <a href="#customers">Customers</a>
                    <a href="#reports">Reports</a>
                    <a slot="footer" href="#settings">Settings</a>
                  </mj-side-nav>
                  <main class="content"><h2>Dashboard</h2><p>Page content.</p></main>
                </div>
            """),
            css=_SIDE_NAV_LAYOUT_CSS,
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="collapsible",
            title="Collapsible rail",
            description="<p><code>mode=\"collapsible\" open</code>: the chevron collapses the panel to a rail that keeps the toggle. Each click logs the cancelable open/close event. Persistence is off here (<code>persist-state=\"false\"</code>).</p>",
            html=_block("""
                <div class="layout">
                  <mj-side-nav id="rail" mode="collapsible" open persist-state="false" nav-label="Projects">
                    <strong slot="header">Projects</strong>
                    <a href="#inbox" aria-current="page">Inbox</a>
                    <a href="#roadmap">Roadmap</a>
                    <a href="#releases">Releases</a>
                  </mj-side-nav>
                  <main class="content"><h2>Inbox</h2><p>Collapse the navigation to give this area more room.</p></main>
                </div>
            """),
            css=_SIDE_NAV_LAYOUT_CSS,
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="overlay-drawer",
            title="Overlay drawer",
            description="<p>The button calls <code>show()</code>; the drawer is modal (the page behind is inert). Close it with Escape, the backdrop or the footer button (<code>hide()</code>). Try <code>edge=\"end\"</code>.</p>",
            html=_block("""
                <mj-side-nav id="drawer" mode="overlay-drawer" nav-label="Site">
                  <strong slot="header">Menu</strong>
                  <a href="#home" aria-current="page">Home</a>
                  <a href="#shop">Shop</a>
                  <a href="#journal">Journal</a>
                  <a href="#contact">Contact</a>
                  <button slot="footer" type="button" id="close-drawer" class="btn">Close</button>
                </mj-side-nav>
                <main class="content">
                  <button type="button" id="open-drawer" class="btn">Open navigation</button>
                  <p>The drawer slides in over this page.</p>
                </main>
            """),
            css=_block("""
                .content { padding: var(--mj-space-4); }
                .btn { min-block-size: var(--mj-control-height-md); padding-inline: var(--mj-space-4); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-md); background: var(--mj-surface); color: var(--mj-text); font: inherit; cursor: pointer; }
            """),
            script=_LINK_GUARD + _block("""
                const drawer = document.getElementById("drawer")
                document.getElementById("open-drawer").addEventListener("click", () => drawer.show())
                document.getElementById("close-drawer").addEventListener("click", () => drawer.hide())
            """),
            height=420,
        ),
        ComponentExample(
            key="keyboard",
            title="Groups and buttons",
            description="<p>Items nested in labelled groups and a button item still form one roving tab stop: Tab in, then ArrowDown / ArrowUp / Home / End. The search field in the header keeps its own keys.</p>",
            html=_block("""
                <div class="layout">
                  <mj-side-nav id="grouped" nav-label="Admin">
                    <input slot="header" type="search" placeholder="Filter" aria-label="Filter sections">
                    <div role="group" aria-labelledby="group-content">
                      <span id="group-content" class="group-label">Content</span>
                      <a href="#pages" aria-current="page">Pages</a>
                      <a href="#media">Media</a>
                    </div>
                    <div role="group" aria-labelledby="group-people">
                      <span id="group-people" class="group-label">People</span>
                      <a href="#users">Users</a>
                      <button type="button" id="invite">Invite user</button>
                    </div>
                  </mj-side-nav>
                  <main class="content"><h2>Pages</h2></main>
                </div>
            """),
            css=_SIDE_NAV_LAYOUT_CSS + _block("""
                #grouped input { inline-size: 100%; box-sizing: border-box; }
                .group-label { display: block; padding: var(--mj-space-3) var(--mj-space-4) var(--mj-space-1); font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); text-transform: uppercase; }
                #grouped [role="group"] a, #grouped [role="group"] button {
                  display: flex; align-items: center; inline-size: 100%; min-block-size: 36px; padding-inline: var(--mj-space-4);
                  border: none; background: none; color: var(--mj-text); font: inherit; text-decoration: none; cursor: pointer; box-sizing: border-box;
                }
                #grouped [aria-current="page"] { color: var(--mj-accent); background: var(--mj-bg-muted); }
            """),
            script=_LINK_GUARD + _block("""
                document.getElementById("invite").addEventListener("click", () => mjSandbox.log("invite dialog would open", {}))
            """),
        ),
        ComponentExample(
            key="persist-state",
            title="Remembered state",
            description="<p>Persistence is on by default in collapsible mode. Collapse the nav, then press Run: it comes back collapsed (stored under <code>persist-key</code> in localStorage).</p>",
            html=_block("""
                <div class="layout">
                  <mj-side-nav id="persisted" mode="collapsible" open persist-key="catalog-demo-side-nav" nav-label="Library">
                    <a href="#books" aria-current="page">Books</a>
                    <a href="#authors">Authors</a>
                    <a href="#loans">Loans</a>
                  </mj-side-nav>
                  <main class="content"><h2>Books</h2><p>Stored value: <output id="stored">-</output></p></main>
                </div>
            """),
            css=_SIDE_NAV_LAYOUT_CSS,
            script=_LINK_GUARD + _block("""
                const output = document.getElementById("stored")
                const show = () => {
                  let value = null
                  try { value = localStorage.getItem("catalog-demo-side-nav") } catch (error) { value = "(storage unavailable)" }
                  output.textContent = value === null ? "nothing yet" : value
                }
                show()
                new MutationObserver(show).observe(document.getElementById("persisted"), { attributes: true, attributeFilter: ["open"] })
            """),
        ),
    ],
    slots=[
        ("", "Navigation items: links or buttons, or wrappers (groups) containing them.", '<a href="#new">New item</a>'),
        ("header", "Content above the items (logo, search).", "<strong>Brand</strong>"),
        ("footer", "Content below the items (settings, account).", '<a href="#help">Help</a>'),
    ],
    properties=[
        ("open", "boolean. Reflects the `open` attribute; setting it emits no event."),
        ("activeItem", "Element | null. The first child with aria-current=\"page\" (read-only)."),
        ("items", "Element[]. The managed navigation items in order (read-only)."),
    ],
    methods=[
        ("show()", "Opens (expands or shows the drawer); emits the cancelable `mj-side-nav-open`."),
        ("hide()", "Closes; emits the cancelable `mj-side-nav-close`."),
    ],
    parts=[
        ("root", "The nav landmark panel (the dialog in an open overlay drawer)."),
        ("header", "Wrapper of the `header` slot."),
        ("nav-list", "Wrapper of the item slot."),
        ("footer", "Wrapper of the `footer` slot."),
        ("toggle", "The collapse / expand button (collapsible mode)."),
        ("backdrop", "Scrim behind an open overlay drawer."),
    ],
    css_properties=[
        ("--mj-side-nav-width", "Panel width (default 240px)."),
        ("--mj-side-nav-collapsed-width", "Width of the collapsed rail (default var(--mj-target-min))."),
        ("--mj-side-nav-bg", "Background (default var(--mj-surface))."),
        ("--mj-side-nav-item-height", "Minimum height of direct item children (default 44px)."),
        ("--mj-side-nav-transition-duration", "Collapse / slide duration (default var(--mj-motion-medium))."),
        ("--mj-side-nav-z-index", "Stacking level of the overlay drawer (default var(--mj-layer-modal))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-breadcrumb
# ---------------------------------------------------------------------------

_BREADCRUMB = ComponentDoc(
    tag="mj-breadcrumb",
    title="Breadcrumb",
    group="navigation",
    summary="A hierarchy trail in a nav landmark that marks the current page and can collapse its middle crumbs.",
    description=(
        "<p><code>&lt;mj-breadcrumb&gt;</code> shows its children as an ordered list inside a "
        "<code>&lt;nav&gt;</code> landmark. The author's elements stay in the light DOM: the component gives "
        "each one a <code>slot=\"mj-crumb-N\"</code> attribute and projects it into its own list item, with a "
        "decorative separator between items.</p>"
        "<p>The current crumb is the one with a <code>current</code> attribute, or else the last one. Its "
        "anchor gets <code>aria-current=\"page\"</code> and loses its <code>href</code> (restored when it "
        "stops being current), so it is not a link to the page you are on.</p>"
        "<p>With <code>max-visible</code> set and more crumbs than that, <code>max-visible</code> crumbs stay "
        "visible: the first one (unless <code>always-show-first=\"false\"</code>) and the trailing ones &mdash; at "
        "least <code>always-show-last</code>, more when <code>max-visible</code> leaves room. The ellipsis "
        "is not counted; when the first and the <code>always-show-last</code> crumbs alone are more than "
        "<code>max-visible</code>, they all stay. The others hide behind an ellipsis button that reveals them "
        "all and focuses the first revealed crumb. A click on a crumb link emits the cancelable "
        "<code>mj-breadcrumb-navigate</code>.</p>"
    ),
    how_to_use=(
        "<p>Put one <code>&lt;a href&gt;</code> per level in the default slot, from the root to the current "
        "page (an element containing an anchor works too). Change the divider with "
        "<code>separator=\"›\"</code> or put an icon in the <code>separator</code> slot (it is cloned between "
        "crumbs). Set <code>max-visible</code> for deep trails. Cancel "
        "<code>mj-breadcrumb-navigate</code> to route client-side.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="separator", description="Divider text between crumbs (ignored when the `separator` slot has content).",
                     kind="string", values=["/", "›", ">", "→", "·"], default="/"),
        AttributeDoc(name="max-visible", description="Number of crumbs shown when the trail collapses (the ellipsis is not counted): with more crumbs than this, the middle ones hide behind an ellipsis. Absent or 0: never collapse.",
                     kind="number"),
        AttributeDoc(name="always-show-first", description="Keep the first crumb visible when collapsed; uncheck (`false`) to hide it too.",
                     kind="boolean", default="true"),
        AttributeDoc(name="always-show-last", description="Minimum number of trailing crumbs kept visible when collapsed (more are shown when `max-visible` leaves room).", kind="number", default="1"),
        AttributeDoc(name="nav-label", description="Accessible name of the nav landmark.", kind="string", default="Breadcrumb"),
    ],
    events=[
        ("mj-breadcrumb-navigate", "Cancelable; a crumb link was clicked. Canceling prevents the navigation.",
         "{ item: Element, href: string, index: number }"),
        ("mj-breadcrumb-expand", "Cancelable; the ellipsis button was activated. Canceling keeps the trail collapsed.", "{}"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>Four levels; the last crumb is the current page (no link, <code>aria-current=\"page\"</code>). Clicking a crumb logs <code>mj-breadcrumb-navigate</code>.</p>",
            html=_block("""
                <mj-breadcrumb id="demo-breadcrumb">
                  <a href="#home">Home</a>
                  <a href="#products">Products</a>
                  <a href="#products/widgets">Widgets</a>
                  <a href="#products/widgets/blue">Blue widget</a>
                </mj-breadcrumb>
            """),
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="collapsed",
            title="Collapsed trail",
            description="<p>Six crumbs with <code>max-visible=\"4\" always-show-last=\"2\"</code>: four stay visible (Home and the last three), the two after Home hide behind the ellipsis. The second trail, <code>max-visible=\"2\" always-show-first=\"false\"</code>, shows only its last two crumbs. Activate an ellipsis to expand.</p>",
            html=_block("""
                <div class="stack">
                  <mj-breadcrumb id="deep-trail" max-visible="4" always-show-last="2" nav-label="Category path">
                    <a href="#home">Home</a>
                    <a href="#electronics">Electronics</a>
                    <a href="#computers">Computers</a>
                    <a href="#laptops">Laptops</a>
                    <a href="#ultrabooks">Ultrabooks</a>
                    <a href="#ultrabooks/aero-14">Aero 14</a>
                  </mj-breadcrumb>
                  <mj-breadcrumb max-visible="2" always-show-first="false" nav-label="Folder path">
                    <a href="#drive">Drive</a>
                    <a href="#team">Team</a>
                    <a href="#team/design">Design</a>
                    <a href="#team/design/logos">Logos</a>
                  </mj-breadcrumb>
                </div>
            """),
            css=".stack { display: grid; gap: var(--mj-space-4); }\n",
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="separators",
            title="Custom separators",
            description="<p>An icon in the <code>separator</code> slot (cloned between crumbs), and the <code>separator</code> attribute.</p>",
            html=_block("""
                <div class="stack">
                  <mj-breadcrumb nav-label="Settings path">
                    <svg slot="separator" viewBox="0 0 16 16" width="12" height="12" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 3l5 5-5 5"/></svg>
                    <a href="#settings">Settings</a>
                    <a href="#settings/security">Security</a>
                    <a href="#settings/security/keys">API keys</a>
                  </mj-breadcrumb>
                  <mj-breadcrumb separator="›" nav-label="Docs path">
                    <a href="#docs">Docs</a>
                    <a href="#docs/guides">Guides</a>
                    <a href="#docs/guides/deploy">Deploy</a>
                  </mj-breadcrumb>
                </div>
            """),
            css=".stack { display: grid; gap: var(--mj-space-4); }\n",
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="explicit-current",
            title="Explicit current",
            description="<p>In a checkout flow the <code>current</code> attribute marks the step you are on; the later crumbs stay links. Move <code>current</code> to another crumb in the HTML pane and Run.</p>",
            html=_block("""
                <mj-breadcrumb id="checkout-trail" separator="→" nav-label="Checkout">
                  <a href="#cart">Cart</a>
                  <a href="#shipping" current>Shipping</a>
                  <a href="#payment">Payment</a>
                  <a href="#review">Review</a>
                </mj-breadcrumb>
            """),
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="events",
            title="Client-side routing",
            description="<p>The script cancels <code>mj-breadcrumb-navigate</code> and shows the chosen level instead; expanding the ellipsis logs <code>mj-breadcrumb-expand</code>.</p>",
            html=_block("""
                <mj-breadcrumb id="routed-trail" max-visible="3">
                  <a href="#/">Home</a>
                  <a href="#/teams">Teams</a>
                  <a href="#/teams/platform">Platform</a>
                  <a href="#/teams/platform/members">Members</a>
                  <a href="#/teams/platform/members/ana">Ana Lima</a>
                </mj-breadcrumb>
                <p>Now viewing: <output id="crumb-view">Ana Lima</output></p>
            """),
            script=_block("""
                const trail = document.getElementById("routed-trail")
                const view = document.getElementById("crumb-view")
                trail.addEventListener("mj-breadcrumb-navigate", (event) => {
                  event.preventDefault()
                  view.textContent = event.detail.item.textContent.trim()
                  mjSandbox.log("routed to crumb", { index: event.detail.index, href: event.detail.href })
                })
            """),
        ),
    ],
    slots=[
        ("", "The crumbs, root first: links, or elements containing a link. The component assigns each a `slot=\"mj-crumb-N\"`.",
         '<a href="#extra">Extra level</a>'),
        ("separator", "Divider content cloned between crumbs; replaces the `separator` text.", '<span aria-hidden="true">»</span>'),
    ],
    properties=[
        ("items", "Element[]. The crumb elements in order (read-only)."),
        ("collapsed", "boolean. True until the ellipsis is expanded; set it to collapse or expand the trail without events."),
    ],
    parts=[
        ("list", "The ordered list."),
        ("item", "Each crumb list item (the current one also has part `current`)."),
        ("current", "The current crumb's list item."),
        ("separator", "Each separator."),
        ("ellipsis", "The list item holding the expand button."),
        ("expand-btn", "The ellipsis button."),
    ],
    css_properties=[
        ("--mj-breadcrumb-font-size", "Font size (default var(--mj-font-size-sm))."),
        ("--mj-breadcrumb-link-color", "Crumb link colour (default var(--mj-accent))."),
        ("--mj-breadcrumb-current-color", "Current crumb colour (default var(--mj-text))."),
        ("--mj-breadcrumb-separator-color", "Separator colour (default var(--mj-text-muted))."),
        ("--mj-breadcrumb-separator-gap", "Space around a separator (default var(--mj-space-2))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-tabs
# ---------------------------------------------------------------------------

_TABS = ComponentDoc(
    tag="mj-tabs",
    title="Tabs",
    group="navigation",
    summary="WAI-ARIA tabs: a tab strip paired with panels by position, activated by click or keyboard.",
    description=(
        "<p><code>&lt;mj-tabs&gt;</code> pairs the elements in the <code>tab</code> slot with the panels in "
        "the default slot by position and wires the ARIA tabs pattern: <code>role=\"tab\"</code> / "
        "<code>tabpanel</code>, <code>aria-selected</code>, <code>aria-controls</code> and "
        "<code>aria-labelledby</code> (ids are generated when missing). The strip is one tab stop.</p>"
        "<p>A click activates a tab. With <code>activation=\"automatic\"</code> (default) the arrow keys "
        "(Left / Right, or Up / Down when vertical; mirrored in RTL), Home and End move focus and selection "
        "together; with <code>manual</code> they move focus only and Enter / Space activates. Tabs with "
        "<code>aria-disabled=\"true\"</code> or <code>disabled</code> are dimmed and skipped. A strip wider "
        "than its container scrolls, with scroll buttons at its edges.</p>"
        "<p><code>variant=\"pills\"</code> renders each tab as a chip and fills the selected one; "
        "<code>enclosed</code> joins the selected tab to the panel; both drop the indicator bar.</p>"
    ),
    how_to_use=(
        "<p>Write one <code>&lt;button slot=\"tab\"&gt;</code> per tab and one panel element per tab, in the "
        "same order. Give tabs ids when you want to select them by id: <code>selected</code> names the "
        "selected tab's id; the component keeps it up to date, and changing it (or calling "
        "<code>select(idOrIndex)</code>) selects that tab without emitting events.</p>"
        "<p>User activation emits the cancelable <code>mj-tabs-change</code> first (cancel it to stay on the "
        "current tab, e.g. with unsaved changes) and <code>mj-tabs-changed</code> once the new panel is "
        "shown.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="selected", description="Id of the selected tab; kept in step by the component. Setting it selects that tab (no events).",
                     kind="string", values=["tab-overview", "tab-specs", "tab-reviews"]),
        AttributeDoc(name="variant", description="Visual style. `pills` and `enclosed` hide the indicator bar.", kind="enum",
                     values=["default", "pills", "enclosed"], default="default"),
        AttributeDoc(name="orientation", description="Tab strip direction; also sets aria-orientation and the arrow keys.", kind="enum",
                     values=["horizontal", "vertical"], default="horizontal"),
        AttributeDoc(name="activation", description="`automatic`: arrow keys select. `manual`: arrow keys move focus, Enter / Space selects.",
                     kind="enum", values=["automatic", "manual"], default="automatic"),
        AttributeDoc(name="tablist-label", description="Accessible name of the tablist.", kind="string", values=["Product details"]),
    ],
    events=[
        ("mj-tabs-change", "Cancelable; the user is activating another tab. Canceling keeps the current tab.",
         "{ selectedId: string, previousId: string, selectedTab: Element, selectedPanel: Element | null }"),
        ("mj-tabs-changed", "The new tab and panel are showing.", "{ selectedId: string, previousId: string }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>Three tabs with ids, so the <code>selected</code> control can pick one. Click a tab or focus the strip and use the arrow keys; each user change logs <code>mj-tabs-change</code> and <code>mj-tabs-changed</code>.</p>",
            html=_block("""
                <mj-tabs id="demo-tabs" tablist-label="Product details">
                  <button slot="tab" type="button" id="tab-overview">Overview</button>
                  <button slot="tab" type="button" id="tab-specs">Specifications</button>
                  <button slot="tab" type="button" id="tab-reviews">Reviews</button>
                  <div><p>The Aero 14 is a 1.2 kg laptop with a 14-inch display and an all-day battery.</p></div>
                  <div><p>14-inch 2880 x 1800 display, 16 GB memory, 1 TB storage, two USB-C ports.</p></div>
                  <div><p>4.6 out of 5 from 128 reviews. "Light, quiet and fast."</p></div>
                </mj-tabs>
            """),
        ),
        ComponentExample(
            key="variants",
            title="Pills and enclosed",
            description="<p><code>variant=\"pills\"</code> fills the selected chip; <code>enclosed</code> joins the selected tab to its panel.</p>",
            html=_block("""
                <div class="stack">
                  <mj-tabs variant="pills" tablist-label="Billing period">
                    <button slot="tab" type="button">Monthly</button>
                    <button slot="tab" type="button">Yearly</button>
                    <div><p>12 EUR per user per month.</p></div>
                    <div><p>120 EUR per user per year (two months free).</p></div>
                  </mj-tabs>
                  <mj-tabs variant="enclosed" tablist-label="Code sample language">
                    <button slot="tab" type="button">Python</button>
                    <button slot="tab" type="button">JavaScript</button>
                    <button slot="tab" type="button">cURL</button>
                    <div><pre>client.orders.list(limit=10)</pre></div>
                    <div><pre>await client.orders.list({ limit: 10 })</pre></div>
                    <div><pre>curl /api/orders?limit=10</pre></div>
                  </mj-tabs>
                </div>
            """),
            css=".stack { display: grid; gap: var(--mj-space-6); }\npre { margin: 0; }\n",
        ),
        ComponentExample(
            key="keyboard",
            title="Vertical, manual activation",
            description="<p><code>orientation=\"vertical\" activation=\"manual\"</code>: ArrowUp / ArrowDown move focus only, Enter or Space selects. Home and End jump to the ends.</p>",
            html=_block("""
                <mj-tabs orientation="vertical" activation="manual" tablist-label="Settings">
                  <button slot="tab" type="button">General</button>
                  <button slot="tab" type="button">Notifications</button>
                  <button slot="tab" type="button">Security</button>
                  <button slot="tab" type="button">Integrations</button>
                  <div><h3>General</h3><p>Workspace name, language and time zone.</p></div>
                  <div><h3>Notifications</h3><p>Choose which events send an e-mail.</p></div>
                  <div><h3>Security</h3><p>Two-factor authentication and active sessions.</p></div>
                  <div><h3>Integrations</h3><p>Connect your calendar and chat tools.</p></div>
                </mj-tabs>
            """),
            css="h3 { margin-block-start: 0; }\n",
        ),
        ComponentExample(
            key="states",
            title="Disabled tab and overflow",
            description="<p>A tab with <code>aria-disabled=\"true\"</code> is dimmed and skipped by the keys. In a narrow container the strip scrolls and shows scroll buttons.</p>",
            html=_block("""
                <div class="narrow">
                  <mj-tabs tablist-label="Report sections">
                    <button slot="tab" type="button">Summary</button>
                    <button slot="tab" type="button">Revenue</button>
                    <button slot="tab" type="button" aria-disabled="true">Forecast (soon)</button>
                    <button slot="tab" type="button">Customers</button>
                    <button slot="tab" type="button">Regions</button>
                    <button slot="tab" type="button">Products</button>
                    <button slot="tab" type="button">Returns</button>
                    <div><p>Revenue grew 12% quarter on quarter.</p></div>
                    <div><p>Revenue by month.</p></div>
                    <div><p>Not available yet.</p></div>
                    <div><p>New and returning customers.</p></div>
                    <div><p>Sales by region.</p></div>
                    <div><p>Best-selling products.</p></div>
                    <div><p>Return rate by category.</p></div>
                  </mj-tabs>
                </div>
            """),
            css=".narrow { max-inline-size: 360px; border: 1px dashed var(--mj-border); }\n",
        ),
        ComponentExample(
            key="events",
            title="Cancel and select()",
            description="<p>Tick <em>unsaved changes</em> and try to leave the Profile tab: the script cancels <code>mj-tabs-change</code>. The button calls <code>select(\"t-billing\")</code>, which changes the tab without events.</p>",
            html=_block("""
                <mj-tabs id="guarded" tablist-label="Account">
                  <button slot="tab" type="button" id="t-profile">Profile</button>
                  <button slot="tab" type="button" id="t-security">Security</button>
                  <button slot="tab" type="button" id="t-billing">Billing</button>
                  <div><label><input type="checkbox" id="dirty"> I have unsaved changes</label></div>
                  <div><p>Password and two-factor settings.</p></div>
                  <div><p>Invoices and payment method.</p></div>
                </mj-tabs>
                <p><button type="button" class="btn" id="go-billing">select("t-billing")</button></p>
            """),
            css=_BTN_CSS,
            script=_block("""
                const tabs = document.getElementById("guarded")
                const dirty = document.getElementById("dirty")
                tabs.addEventListener("mj-tabs-change", (event) => {
                  if (dirty.checked && event.detail.previousId === "t-profile") {
                    event.preventDefault()
                    mjSandbox.log("change canceled: unsaved changes", { wanted: event.detail.selectedId })
                  }
                })
                document.getElementById("go-billing").addEventListener("click", () => {
                  const selected = tabs.select("t-billing")
                  mjSandbox.log("select() returned", { selected: selected, now: tabs.selected })
                })
            """),
        ),
    ],
    slots=[
        ("tab", "The tab buttons, in order.", '<button type="button">New tab</button>'),
        ("", "The panels, one per tab, in the same order.", "<div><p>New panel content.</p></div>"),
    ],
    properties=[
        ("selected", "string. Id of the selected tab (\"\" when none); setting it calls `select()`."),
        ("selectedTab", "Element | null. The selected tab (read-only)."),
        ("selectedPanel", "Element | null. The selected panel (read-only)."),
        ("tabs", "Element[]. The tab elements (read-only copy)."),
    ],
    methods=[
        ("select(idOrIndex) -> boolean", "Selects a tab by id or index without events; false when it does not exist or is disabled."),
    ],
    parts=[
        ("tablist", "The tab strip (role tablist)."),
        ("indicator", "The bar under (or beside) the selected tab."),
        ("panels", "Wrapper of the panel slot."),
        ("scroll-prev", "Scroll button at the start of an overflowing strip."),
        ("scroll-next", "Scroll button at the end of an overflowing strip."),
    ],
    css_properties=[
        ("--mj-tabs-tab-gap", "Gap between tabs (default var(--mj-space-1))."),
        ("--mj-tabs-tab-padding", "Tab padding (default var(--mj-space-2) var(--mj-space-4))."),
        ("--mj-tabs-font-weight-selected", "Weight of the selected tab (default 600)."),
        ("--mj-tabs-indicator-height", "Thickness of the indicator (default 2px)."),
        ("--mj-tabs-indicator-color", "Indicator colour (default var(--mj-accent))."),
        ("--mj-tabs-transition-duration", "Indicator animation duration (default var(--mj-motion-fast))."),
        ("--mj-tabs-panel-padding", "Panel padding (default var(--mj-space-5))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-nav-stepper
# ---------------------------------------------------------------------------

_NAV_STEPPER = ComponentDoc(
    tag="mj-nav-stepper",
    title="Nav Stepper",
    group="navigation",
    summary="An ordered step indicator for multi-step flows with complete, current, upcoming, error and disabled steps.",
    description=(
        "<p><code>&lt;mj-nav-stepper&gt;</code> renders an ordered list of step buttons from its children. "
        "The slotted elements are only data (their text is the label, their <code>status</code> attribute "
        "the state); they are not displayed. The list is rebuilt when <code>current</code>, a step, its text "
        "or its <code>status</code> changes.</p>"
        "<p>Each step's status is its <code>status</code> attribute when that is <code>complete</code>, "
        "<code>error</code> or <code>disabled</code>; otherwise it follows from <code>current</code> "
        "(before: complete, at: current, after: upcoming). Complete steps show a check mark, error steps an "
        "exclamation mark; the current step has <code>aria-current=\"step\"</code>.</p>"
        "<p>Complete and error steps can always be clicked; in non-linear mode (<code>linear=\"false\"</code>) "
        "every step except disabled ones can. Others get <code>aria-disabled=\"true\"</code> and leave the tab "
        "order. A click emits the cancelable <code>mj-nav-stepper-change</code> and then moves "
        "<code>current</code>. When every step becomes complete &mdash; through <code>status</code> changes, or "
        "by moving <code>current</code> past the last step &mdash; <code>mj-nav-stepper-complete</code> fires "
        "(once per transition; a stepper that loads complete does not fire it).</p>"
    ),
    how_to_use=(
        "<p>Put one element per step in the default slot (e.g. <code>&lt;span&gt;Payment&lt;/span&gt;</code>) "
        "and set <code>current</code> to the zero-based index of the active step; move it as the user "
        "progresses. Mark a failed step with <code>status=\"error\"</code> and an unavailable one with "
        "<code>status=\"disabled\"</code>. Use <code>orientation=\"vertical\"</code> in a sidebar and "
        "<code>compact</code> where only the circles fit (the label becomes a tooltip). For a complete flow "
        "with panels and buttons use <code>&lt;mj-wizard&gt;</code>.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="current", description="Zero-based index of the current step; the step count (or more) marks every step complete.", kind="number", default="0"),
        AttributeDoc(name="orientation", description="Row or column of steps (vertical connectors run under the circles).", kind="enum",
                     values=["horizontal", "vertical"], default="horizontal"),
        AttributeDoc(name="linear", description="Upcoming steps cannot be clicked; uncheck (`false`) to allow jumping to any step that is not disabled.",
                     kind="boolean", default="true"),
        AttributeDoc(name="compact", description="Hides the labels (shown as a tooltip) and keeps only the circles.", kind="boolean"),
        AttributeDoc(name="label", description="Accessible name of the list.", kind="string", default="Progress"),
    ],
    events=[
        ("mj-nav-stepper-change", "Cancelable; a navigable step was clicked. Canceling keeps `current`.",
         "{ index: number, previousIndex: number, step: Element }"),
        ("mj-nav-stepper-complete", "Every step became complete (a `status` change, or `current` moved past the last step).", "{ completedCount: number, total: number }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>Four steps with the second current: the first is complete and clickable, the later ones are upcoming and disabled (linear mode).</p>",
            html=_block("""
                <mj-nav-stepper id="demo-stepper" current="1" label="Checkout progress">
                  <span>Cart</span>
                  <span>Shipping</span>
                  <span>Payment</span>
                  <span>Review</span>
                </mj-nav-stepper>
            """),
        ),
        ComponentExample(
            key="vertical",
            title="Vertical",
            description="<p><code>orientation=\"vertical\"</code> stacks the steps with connectors under the circles, for a sidebar.</p>",
            html=_block("""
                <mj-nav-stepper orientation="vertical" current="2" label="Onboarding">
                  <span>Create account</span>
                  <span>Verify e-mail</span>
                  <span>Invite your team</span>
                  <span>Connect a data source</span>
                </mj-nav-stepper>
            """),
        ),
        ComponentExample(
            key="compact",
            title="Compact",
            description="<p><code>compact</code> keeps only the circles; each label is the button's tooltip and accessible name.</p>",
            html=_block("""
                <mj-nav-stepper compact current="3" label="Survey progress">
                  <span>About you</span>
                  <span>Your team</span>
                  <span>Tools</span>
                  <span>Workflow</span>
                  <span>Feedback</span>
                  <span>Done</span>
                </mj-nav-stepper>
            """),
            css="mj-nav-stepper { max-inline-size: 420px; }\n",
        ),
        ComponentExample(
            key="states",
            title="Statuses, non-linear",
            description="<p><code>linear=\"false\"</code> with explicit statuses: <code>complete</code>, <code>error</code> and <code>disabled</code>. Every step except the disabled one can be clicked.</p>",
            html=_block("""
                <mj-nav-stepper current="1" linear="false" label="Import">
                  <span status="complete">Upload file</span>
                  <span>Map columns</span>
                  <span status="error">Validate rows</span>
                  <span status="disabled">Schedule</span>
                  <span>Confirm</span>
                </mj-nav-stepper>
            """),
        ),
        ComponentExample(
            key="events",
            title="Driven by buttons",
            description="<p>Back / Next move <code>current</code>; clicking a completed step logs <code>mj-nav-stepper-change</code>. <em>Next</em> on the last step moves <code>current</code> past it: every step is complete and <code>mj-nav-stepper-complete</code> fires. <em>Mark all complete</em> does the same through <code>status=\"complete\"</code> on every step.</p>",
            html=_block("""
                <mj-nav-stepper id="driven" current="0" label="Application">
                  <span>Personal details</span>
                  <span>Experience</span>
                  <span>Documents</span>
                </mj-nav-stepper>
                <p class="row">
                  <button type="button" class="btn" id="step-back">Back</button>
                  <button type="button" class="btn" id="step-next">Next</button>
                  <button type="button" class="btn" id="step-done">Mark all complete</button>
                </p>
            """),
            css=_BTN_CSS + ".row { display: flex; gap: var(--mj-space-2); }\n",
            script=_block("""
                const stepper = document.getElementById("driven")
                const move = (delta) => {
                  // `current` may go one past the last step: the flow is finished.
                  const finished = stepper.steps.length
                  const next = Math.min(finished, Math.max(0, Number(stepper.getAttribute("current")) + delta))
                  stepper.setAttribute("current", String(next))
                  mjSandbox.log("current", { current: next, completedCount: stepper.completedCount })
                }
                document.getElementById("step-back").addEventListener("click", () => move(-1))
                document.getElementById("step-next").addEventListener("click", () => move(1))
                document.getElementById("step-done").addEventListener("click", () => {
                  for (const step of stepper.steps) { step.setAttribute("status", "complete") }
                })
            """),
        ),
    ],
    slots=[
        ("", "One element per step: its text is the label, its `status` attribute (complete, error, disabled) overrides the derived state. Not displayed itself.",
         "<span>New step</span>"),
    ],
    properties=[
        ("steps", "Element[]. The slotted step elements (read-only)."),
        ("currentStep", "Element | null. The step at `current` (read-only)."),
        ("completedCount", "number. Steps rendered as complete, explicitly or by position (read-only)."),
    ],
    parts=[
        ("list", "The ordered list."),
        ("step", "Each list item (`data-status` holds its status)."),
        ("link", "Each step button."),
        ("indicator", "The numbered / check / error circle."),
        ("label", "The step label."),
        ("connector", "The line between steps."),
    ],
    css_properties=[
        ("--mj-nav-stepper-font-size", "Label font size (default var(--mj-font-size-sm))."),
        ("--mj-nav-stepper-indicator-size", "Circle diameter (default 32px)."),
        ("--mj-nav-stepper-indicator-bg-upcoming", "Upcoming circle (default var(--mj-bg-muted))."),
        ("--mj-nav-stepper-indicator-bg-current", "Current circle (default var(--mj-accent))."),
        ("--mj-nav-stepper-indicator-bg-complete", "Complete circle (default var(--mj-color-success))."),
        ("--mj-nav-stepper-indicator-color-complete", "Check mark colour (default var(--mj-text-on-accent))."),
        ("--mj-nav-stepper-indicator-bg-error", "Error circle (default var(--mj-color-danger))."),
        ("--mj-nav-stepper-indicator-color-error", "Error mark colour (default var(--mj-text-on-accent))."),
        ("--mj-nav-stepper-connector-width", "Connector thickness (default 2px)."),
        ("--mj-nav-stepper-connector-color", "Connector colour (default var(--mj-border))."),
        ("--mj-nav-stepper-connector-color-complete", "Connector after a complete step (default var(--mj-color-success))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-wizard
# ---------------------------------------------------------------------------

_WIZARD_CSS = _block("""
    mj-wizard h3 { margin-block-start: 0; }
    mj-wizard label { display: grid; gap: var(--mj-space-1); max-inline-size: 320px; margin-block-end: var(--mj-space-3); }
    mj-wizard input, mj-wizard select { font: inherit; padding: var(--mj-space-2); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); background: var(--mj-surface); color: var(--mj-text); }
    mj-wizard label.inline { display: flex; align-items: center; gap: var(--mj-space-2); }
""")

_WIZARD = ComponentDoc(
    tag="mj-wizard",
    title="Wizard",
    group="navigation",
    summary="A multi-step flow with an embedded stepper, Back / Next / Submit buttons and per-step validation.",
    description=(
        "<p><code>&lt;mj-wizard&gt;</code> shows one of its child elements (the steps) at a time, with an "
        "<code>&lt;mj-nav-stepper&gt;</code> above (or beside) it and a button bar below. Step titles come "
        "from the step's <code>label</code> attribute, else its first <code>h2</code>, <code>h3</code> or "
        "<code>[data-title]</code>, else &ldquo;Step N&rdquo;. The inactive steps get <code>hidden</code>, the "
        "active one <code>data-active</code>.</p>"
        "<p>The buttons, a click on a completed step in the stepper, and <code>next()</code> / "
        "<code>back()</code> / <code>goTo()</code> all take one path: in linear mode (default) moving forward "
        "first validates the current step (every form, native control and mj-* form control in it; the first "
        "invalid one reports its message), then the cancelable <code>mj-wizard-before-change</code> fires "
        "(direction <code>next</code>, <code>back</code> or <code>jump</code>), then the step changes, focus "
        "moves into it and a live region announces &ldquo;Step N of M: title&rdquo;. Nothing takes focus on "
        "load.</p>"
        "<p>Submit validates the last step as well, then emits the cancelable <code>mj-wizard-submit</code> "
        "with a <code>FormData</code> of every <code>&lt;form&gt;</code> inside the wizard (<code>null</code> "
        "when there is none) and, unless canceled, <code>mj-wizard-complete</code>.</p>"
    ),
    how_to_use=(
        "<p>Write one element per step (a <code>&lt;section label=\"...\"&gt;</code> is a good fit) and put the "
        "fields of each step in a <code>&lt;form&gt;</code> with named inputs if you want the submitted "
        "<code>FormData</code>; mark mandatory fields <code>required</code>. Prevent the forms' native submit "
        "(Enter in a field), e.g. by calling <code>wizard.next()</code> instead. Rename the buttons with "
        "<code>next-label</code>, <code>back-label</code> and <code>submit-label</code>, or replace the bar "
        "with your own buttons in the <code>actions</code> slot and call the methods from them.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="current", description="Zero-based index of the shown step (clamped); kept in step by the wizard. Setting it switches without validation or events.",
                     kind="number", default="0"),
        AttributeDoc(name="linear", description="Validate the current step before moving forward and submitting; uncheck (`false`) to allow free movement.",
                     kind="boolean", default="true"),
        AttributeDoc(name="stepper-position", description="Where the stepper sits; `side` puts a vertical stepper in a column at the inline start; the step content and, below it, the button bar fill the other column.", kind="enum",
                     values=["top", "side", "none"], default="top"),
        AttributeDoc(name="label", description="Accessible name of the wizard group.", kind="string", default="Wizard"),
        AttributeDoc(name="next-label", description="Next button text.", kind="string", values=["Continue"], default="Next"),
        AttributeDoc(name="back-label", description="Back button text.", kind="string", values=["Previous"], default="Back"),
        AttributeDoc(name="submit-label", description="Submit button text (last step).", kind="string", values=["Create account", "Place order"], default="Submit"),
    ],
    events=[
        ("mj-wizard-before-change", "Cancelable; a user-driven step change passed validation. Canceling stays on the step.",
         "{ from: number, to: number, direction: 'next' | 'back' | 'jump' }"),
        ("mj-wizard-step-leave", "The step being left.", "{ index: number, step: Element }"),
        ("mj-wizard-step-enter", "The step now shown.", "{ index: number, step: Element }"),
        ("mj-wizard-change", "The step change finished.", "{ from: number, to: number, direction: 'next' | 'back' | 'jump' }"),
        ("mj-wizard-submit", "Cancelable; Submit passed validation. Canceling skips mj-wizard-complete.", "{ formData: FormData | null }"),
        ("mj-wizard-complete", "Fired after a mj-wizard-submit that was not canceled.", "{}"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>A sign-up flow. Next is blocked until the required field is valid; Enter in a field also moves on. The review step is filled from the entered values, and Submit logs the collected <code>FormData</code>.</p>",
            html=_block("""
                <mj-wizard id="signup-wizard" label="Sign up" submit-label="Create account">
                  <section label="Account">
                    <h3>Create your account</h3>
                    <form><label>Work e-mail <input name="email" type="email" required autocomplete="off"></label></form>
                  </section>
                  <section label="Profile">
                    <h3>About you</h3>
                    <form><label>Full name <input name="name" required autocomplete="off"></label></form>
                  </section>
                  <section label="Review">
                    <h3>Review</h3>
                    <p id="signup-summary">Check your details, then create the account.</p>
                  </section>
                </mj-wizard>
            """),
            css=_WIZARD_CSS,
            script=_block("""
                const wizard = document.getElementById("signup-wizard")
                if (wizard !== null) {
                  for (const form of wizard.querySelectorAll("form")) {
                    // Enter in a field submits its form, which would reload the preview: move on instead.
                    form.addEventListener("submit", (event) => {
                      event.preventDefault()
                      if (wizard.isLastStep) { wizard.submit() } else { wizard.next() }
                    })
                  }
                  wizard.addEventListener("mj-wizard-step-enter", (event) => {
                    if (event.detail.index === wizard.steps.length - 1) {
                      const email = wizard.querySelector("[name=email]").value
                      const name = wizard.querySelector("[name=name]").value
                      document.getElementById("signup-summary").textContent = name + " <" + email + ">"
                    }
                  })
                  wizard.addEventListener("mj-wizard-submit", (event) => {
                    const data = event.detail.formData !== null ? Object.fromEntries(event.detail.formData) : null
                    mjSandbox.log("submitted", data)
                  })
                }
            """),
        ),
        ComponentExample(
            key="side-stepper",
            title="Side stepper, custom labels",
            description="<p><code>stepper-position=\"side\"</code> with <code>next-label</code>, <code>back-label</code> and <code>submit-label</code>. No required fields, so Continue always moves on.</p>",
            html=_block("""
                <mj-wizard label="Checkout" stepper-position="side" next-label="Continue" back-label="Previous" submit-label="Place order">
                  <section label="Cart"><h3>Cart</h3><p>2 items, 84.00 EUR.</p></section>
                  <section label="Shipping">
                    <h3>Shipping</h3>
                    <label>Method
                      <select><option>Standard (3-5 days)</option><option>Express (next day)</option></select>
                    </label>
                  </section>
                  <section label="Payment"><h3>Payment</h3><p>Card ending in 4242.</p></section>
                  <section label="Confirm"><h3>Confirm</h3><p>Ready to place your order.</p></section>
                </mj-wizard>
            """),
            css=_WIZARD_CSS,
        ),
        ComponentExample(
            key="non-linear",
            title="Non-linear",
            description="<p><code>linear=\"false\"</code>: the required field does not block, and every step in the stepper can be clicked (direction <code>jump</code> in the log).</p>",
            html=_block("""
                <mj-wizard label="Project settings" linear="false">
                  <section label="General"><h3>General</h3><label>Project name <input required></label></section>
                  <section label="Members"><h3>Members</h3><p>3 members.</p></section>
                  <section label="Billing"><h3>Billing</h3><p>Team plan.</p></section>
                  <section label="Danger zone"><h3>Danger zone</h3><p>Archive or delete the project.</p></section>
                </mj-wizard>
            """),
            css=_WIZARD_CSS,
        ),
        ComponentExample(
            key="custom-actions",
            title="Own buttons (actions slot)",
            description="<p><code>stepper-position=\"none\"</code> and a custom bar in the <code>actions</code> slot; the buttons call <code>back()</code>, <code>next()</code>, <code>goTo(0)</code> and <code>submit()</code> and read <code>isFirstStep</code> / <code>isLastStep</code>.</p>",
            html=_block("""
                <mj-wizard id="survey" label="Survey" stepper-position="none">
                  <section><h3>How did you hear about us?</h3><label class="inline"><input type="radio" name="source" checked> A colleague</label><label class="inline"><input type="radio" name="source"> A search engine</label></section>
                  <section><h3>How often do you use the product?</h3><label class="inline"><input type="radio" name="use" checked> Daily</label><label class="inline"><input type="radio" name="use"> Weekly</label></section>
                  <section><h3>Anything else?</h3><label>Comment <input name="comment"></label></section>
                  <div slot="actions" class="actions">
                    <button type="button" id="survey-restart">Start over</button>
                    <span id="survey-progress">Question 1 of 3</span>
                    <button type="button" id="survey-back">Back</button>
                    <button type="button" id="survey-next">Next question</button>
                  </div>
                </mj-wizard>
            """),
            css=_WIZARD_CSS + _block("""
                .actions { display: flex; align-items: center; gap: var(--mj-space-2); inline-size: 100%; }
                #survey-progress { margin-inline-start: auto; color: var(--mj-text-muted); }
                .actions button { min-block-size: var(--mj-control-height-md); padding-inline: var(--mj-space-4); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-md); background: var(--mj-surface); color: var(--mj-text); font: inherit; cursor: pointer; }
                .actions button:disabled { opacity: 0.5; cursor: not-allowed; }
                #survey-next { background: var(--mj-accent); border-color: var(--mj-accent); color: var(--mj-text-on-accent); }
            """),
            script=_block("""
                const survey = document.getElementById("survey")
                const progress = document.getElementById("survey-progress")
                const back = document.getElementById("survey-back")
                const next = document.getElementById("survey-next")
                const sync = () => {
                  progress.textContent = "Question " + (Number(survey.getAttribute("current")) + 1) + " of " + survey.steps.length
                  back.disabled = survey.isFirstStep
                  next.textContent = survey.isLastStep ? "Send answers" : "Next question"
                }
                back.addEventListener("click", () => survey.back())
                next.addEventListener("click", () => { if (survey.isLastStep) { survey.submit() } else { survey.next() } })
                document.getElementById("survey-restart").addEventListener("click", () => survey.goTo(0))
                survey.addEventListener("mj-wizard-change", sync)
                survey.addEventListener("mj-wizard-complete", () => mjSandbox.log("survey sent", {}))
                sync()
            """),
        ),
        ComponentExample(
            key="events",
            title="Guarding a step change",
            description="<p>While <em>Lock this step</em> is ticked the script cancels <code>mj-wizard-before-change</code>. The Events panel shows the full sequence of a change: before-change, step-leave, step-enter, change.</p>",
            html=_block("""
                <label class="lock"><input type="checkbox" id="lock-step"> Lock this step</label>
                <mj-wizard id="guarded-wizard" label="Deployment">
                  <section label="Build"><h3>Build</h3><p>Commit 4f2a9c built in 2 min.</p></section>
                  <section label="Test"><h3>Test</h3><p>214 tests passed.</p></section>
                  <section label="Release"><h3>Release</h3><p>Promote the build to production.</p></section>
                </mj-wizard>
            """),
            css=_WIZARD_CSS + ".lock { display: flex; gap: var(--mj-space-2); margin-block-end: var(--mj-space-3); }\n",
            script=_block("""
                const wizard = document.getElementById("guarded-wizard")
                const lock = document.getElementById("lock-step")
                wizard.addEventListener("mj-wizard-before-change", (event) => {
                  if (lock.checked) {
                    event.preventDefault()
                    mjSandbox.log("step change canceled", event.detail)
                  }
                })
                wizard.addEventListener("mj-wizard-submit", (event) => {
                  event.preventDefault()
                  mjSandbox.log("submit canceled: release needs approval", {})
                })
            """),
        ),
    ],
    slots=[
        ("", "The steps, one element each (label attribute, or an h2 / h3 / [data-title] as title).",
         '<section label="Extra step"><h3>Extra step</h3><p>Added by the slot inspector.</p></section>'),
        ("actions", "Replaces the built-in Back / Next / Submit bar; wire your buttons to the methods.",
         '<div><button type="button">Save draft</button></div>'),
    ],
    properties=[
        ("steps", "Element[]. The step elements (read-only copy)."),
        ("currentStep", "Element | null. The shown step (read-only)."),
        ("isFirstStep", "boolean. True on the first step (read-only)."),
        ("isLastStep", "boolean. True on the last step (read-only)."),
        ("valid", "boolean. Whether the current step's controls are all valid; reports nothing (read-only)."),
    ],
    methods=[
        ("next() -> boolean", "Goes to the next step (validation in linear mode, then mj-wizard-before-change); true when it moved."),
        ("back() -> boolean", "Goes to the previous step; true when it moved."),
        ("goTo(index) -> boolean", "Jumps to a step (direction `jump`; forward jumps validate in linear mode); true when it moved."),
        ("submit() -> boolean", "Validates the current step (linear) and emits mj-wizard-submit / mj-wizard-complete; true when completed."),
    ],
    parts=[
        ("root", "The wizard group."),
        ("stepper", "Area holding the embedded mj-nav-stepper."),
        ("content", "Scrolling content area."),
        ("panel", "Focusable wrapper of the step slot."),
        ("nav-bar", "The button bar (holds the `actions` slot)."),
        ("back-btn", "Built-in Back button."),
        ("next-btn", "Built-in Next button."),
        ("submit-btn", "Built-in Submit button."),
    ],
    css_properties=[
        ("--mj-wizard-min-height", "Minimum height (default 320px)."),
        ("--mj-wizard-stepper-width", "Width of the side stepper (default 200px)."),
        ("--mj-wizard-content-padding", "Padding of the step area (default var(--mj-space-6))."),
        ("--mj-wizard-nav-bar-padding", "Padding of the button bar (default var(--mj-space-4) var(--mj-space-6))."),
        ("--mj-wizard-nav-bar-border", "Border above the button bar (default 1px solid var(--mj-border))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-pagination
# ---------------------------------------------------------------------------

_PAGINATION = ComponentDoc(
    tag="mj-pagination",
    title="Pagination",
    group="navigation",
    summary="Page navigation with Previous / Next, numbered pages with ellipsis, a results summary and an optional page-size selector.",
    description=(
        "<p><code>&lt;mj-pagination&gt;</code> renders a <code>&lt;nav&gt;</code> landmark with Previous and "
        "Next and, in the <code>full</code> variant, numbered pages: the first and last "
        "<code>boundary-count</code> pages and <code>sibling-count</code> pages on each side of the current "
        "one, with an ellipsis for the gaps. <code>compact</code> shows &ldquo;Page X of Y&rdquo; instead, "
        "<code>simple</code> only the two arrows.</p>"
        "<p>The page count is <code>total-pages</code> when set, else derived from <code>total-items</code> "
        "and <code>page-size</code>. With <code>total-items</code> a &ldquo;Showing X&ndash;Y of Z&rdquo; "
        "summary appears (<code>hide-summary</code> removes it, <code>show-summary</code> forces it). When "
        "there is only one page the host gets the read-only <code>single-page</code> attribute and hides "
        "itself, unless <code>show-single-page</code> is set.</p>"
        "<p>With <code>href-template</code> the controls are real links (<code>{page}</code> is replaced by "
        "the page number); modified clicks (Ctrl, Shift ...) are left to the browser. "
        "<code>show-page-size</code> adds a page-size selector. Keyboard focus stays on the equivalent control "
        "after every change.</p>"
    ),
    how_to_use=(
        "<p>Set <code>page</code> (1-based) and <code>total-items</code> (with <code>page-size</code>) or "
        "<code>total-pages</code>. The pager updates its own <code>page</code> on a click; listen for "
        "<code>mj-pagination-change</code> to load the page (use <code>event.detail.page</code>: the attribute "
        "changes after the event) or cancel it to keep the page. "
        "<code>mj-pagination-page-size-change</code> (cancelable) is followed by a non-cancelable "
        "<code>mj-pagination-change</code> that keeps the first item of the old page in view. Replace the "
        "arrow labels with the <code>prev-label</code> / <code>next-label</code> slots and the summary text "
        "with the <code>summary</code> slot.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="page", description="Current page, 1-based (clamped to the page count).", kind="number", default="1"),
        AttributeDoc(name="total-pages", description="Page count; when absent it is derived from total-items / page-size.", kind="number"),
        AttributeDoc(name="total-items", description="Number of records; drives the derived page count and the summary.", kind="number"),
        AttributeDoc(name="page-size", description="Records per page.", kind="number", default="10"),
        AttributeDoc(name="sibling-count", description="Page buttons on each side of the current page.", kind="number", default="1"),
        AttributeDoc(name="boundary-count", description="Page buttons always shown at each end.", kind="number", default="1"),
        AttributeDoc(name="variant", description="`full` numbered list, `compact` \"Page X of Y\", `simple` arrows only.", kind="enum",
                     values=["full", "compact", "simple"], default="full"),
        AttributeDoc(name="show-summary", description="Always show the results summary.", kind="boolean"),
        AttributeDoc(name="hide-summary", description="Hide the summary that total-items would show.", kind="boolean"),
        AttributeDoc(name="show-single-page", description="Keep the pager visible when there is only one page.", kind="boolean"),
        AttributeDoc(name="show-page-size", description="Add the \"Items per page\" selector.", kind="boolean"),
        AttributeDoc(name="page-size-options", description="Comma-separated sizes for the selector (the current size is always included).",
                     kind="string", values=["5,10,20", "10,25,50,100"], default="10,25,50,100"),
        AttributeDoc(name="href-template", description="Renders the controls as links; `{page}` is replaced with the page number.",
                     kind="string", values=["?page={page}", "#results-page-{page}"]),
        AttributeDoc(name="disabled", description="Disables Previous / Next and the selector; page buttons stay focusable but inert.", kind="boolean"),
        AttributeDoc(name="nav-label", description="Accessible name of the nav landmark.", kind="string", default="Pagination"),
    ],
    events=[
        ("mj-pagination-change", "A page control was activated (cancelable: canceling keeps the page), or the page size changed (not cancelable).",
         "{ page: number, previousPage: number, pageSize: number }"),
        ("mj-pagination-page-size-change", "Cancelable; a new size was picked in the selector. Canceling restores the selection.",
         "{ pageSize: number, previousPageSize: number }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>97 records at 10 per page give 10 pages; the summary comes from <code>total-items</code>. Click a page or Next; each move logs <code>mj-pagination-change</code>.</p>",
            html=_block("""
                <mj-pagination id="demo-pager" page="3" total-items="97" page-size="10"></mj-pagination>
            """),
        ),
        ComponentExample(
            key="variants",
            title="Variants",
            description="<p><code>full</code> (default), <code>compact</code> and <code>simple</code> on the same 20 pages.</p>",
            html=_block("""
                <div class="stack">
                  <mj-pagination variant="compact" page="4" total-pages="20" nav-label="Compact pager"></mj-pagination>
                  <mj-pagination page="4" total-pages="20" nav-label="Full pager"></mj-pagination>
                  <mj-pagination variant="simple" page="4" total-pages="20" nav-label="Simple pager"></mj-pagination>
                </div>
            """),
            css=".stack { display: grid; gap: var(--mj-space-4); }\n",
        ),
        ComponentExample(
            key="large-data",
            title="Many pages",
            description="<p>500 pages with <code>sibling-count=\"2\" boundary-count=\"2\"</code>: two pages at each end and two around the current one.</p>",
            html=_block("""
                <mj-pagination page="250" total-pages="500" sibling-count="2" boundary-count="2"></mj-pagination>
            """),
        ),
        ComponentExample(
            key="events",
            title="Driving a list",
            description="<p>The script renders the orders of the current page from <code>event.detail</code> and <code>pageRange</code>. Change the page size in the selector: <code>mj-pagination-page-size-change</code> is followed by <code>mj-pagination-change</code>.</p>",
            html=_block("""
                <ol id="orders" class="orders"></ol>
                <mj-pagination id="orders-pager" page="1" total-items="42" page-size="5" show-page-size page-size-options="5,10,20" nav-label="Orders pages"></mj-pagination>
            """),
            css=".orders { margin: 0 0 var(--mj-space-4); padding-inline-start: var(--mj-space-6); min-block-size: 8em; }\n",
            script=_block("""
                const pager = document.getElementById("orders-pager")
                const list = document.getElementById("orders")
                const orders = Array.from({ length: 42 }, (_, i) => ({ id: 1001 + i, total: ((i * 37) % 250) + 20 }))
                const render = (first, last) => {
                  list.start = first + 1
                  list.replaceChildren(...orders.slice(first, last + 1).map((order) => {
                    const item = document.createElement("li")
                    item.textContent = "Order #" + order.id + " - " + order.total + ".00 EUR"
                    return item
                  }))
                }
                pager.addEventListener("mj-pagination-change", (event) => {
                  // The page attribute changes after this event: use the detail.
                  const first = (event.detail.page - 1) * event.detail.pageSize
                  render(first, Math.min(first + event.detail.pageSize, orders.length) - 1)
                })
                const [first, last] = pager.pageRange
                render(first, last)
            """),
        ),
        ComponentExample(
            key="states",
            title="Disabled, single page, no summary",
            description="<p>A <code>disabled</code> pager; a single page kept visible with <code>show-single-page</code> (without it the pager hides itself); and <code>hide-summary</code>.</p>",
            html=_block("""
                <div class="stack">
                  <mj-pagination disabled page="2" total-items="64" page-size="10" nav-label="Disabled pager"></mj-pagination>
                  <mj-pagination show-single-page total-items="8" page-size="10" nav-label="Single page"></mj-pagination>
                  <mj-pagination total-items="8" page-size="10" nav-label="Hidden single page"></mj-pagination>
                  <mj-pagination hide-summary page="2" total-items="64" page-size="10" nav-label="Without summary"></mj-pagination>
                </div>
            """),
            css=".stack { display: grid; gap: var(--mj-space-4); }\n",
        ),
        ComponentExample(
            key="links",
            title="Links and custom labels",
            description="<p><code>href-template</code> turns the controls into links (the preview logs instead of following them); the <code>prev-label</code> / <code>next-label</code> slots replace the arrow labels.</p>",
            html=_block("""
                <mj-pagination id="linked-pager" page="2" total-pages="8" href-template="#results-page-{page}" nav-label="Search results pages">
                  <span slot="prev-label">&larr; Newer</span>
                  <span slot="next-label">Older &rarr;</span>
                </mj-pagination>
            """),
            script=_LINK_GUARD,
        ),
    ],
    slots=[
        ("prev-label", "Replaces the \"Previous\" label and arrow.", "<span>&lsaquo; Back</span>"),
        ("next-label", "Replaces the \"Next\" label and arrow.", "<span>More &rsaquo;</span>"),
        ("summary", "Replaces the summary text (shown only while the summary is visible).", "<span>Lots of results</span>"),
    ],
    properties=[
        ("totalPages", "number. The page count, explicit or derived (read-only)."),
        ("hasPrevious", "boolean. Whether there is a page before the current one (read-only)."),
        ("hasNext", "boolean. Whether there is a page after the current one (read-only)."),
        ("pageRange", "[number, number]. 0-based indexes of the first and last record of the current page (read-only)."),
    ],
    parts=[
        ("nav", "The nav landmark."),
        ("root", "The row holding every control."),
        ("prev", "The Previous control."),
        ("next", "The Next control."),
        ("page-list", "The list of page numbers (full variant)."),
        ("page-item", "Each list item holding a page button."),
        ("page-btn", "Each page number button or link."),
        ("ellipsis", "Each list item holding an ellipsis."),
        ("compact-label", "The \"Page X of Y\" label (compact variant)."),
        ("page-size", "The page-size selector label."),
        ("summary", "The results summary."),
    ],
    css_properties=[
        ("--mj-pagination-font-size", "Font size (default var(--mj-font-size-sm))."),
        ("--mj-pagination-btn-size", "Button height and minimum width (default 36px)."),
        ("--mj-pagination-btn-gap", "Gap between page buttons (default var(--mj-space-1))."),
        ("--mj-pagination-btn-radius", "Button corner radius (default var(--mj-radius-sm))."),
        ("--mj-pagination-current-bg", "Current page background (default var(--mj-accent))."),
        ("--mj-pagination-current-color", "Current page text (default var(--mj-text-on-accent))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-toc
# ---------------------------------------------------------------------------

_TOC_CSS = _block("""
    .doc { display: flex; gap: var(--mj-space-5); align-items: flex-start; }
    .scroller { flex: 1; min-inline-size: 0; block-size: 300px; overflow: auto; padding-inline: var(--mj-space-4); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
    .scroller::after { content: ""; display: block; block-size: 220px; }
    .scroller:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: 2px; }
    .scroller p { color: var(--mj-text-muted); }
    @media (max-width: 560px) { .doc { flex-direction: column; } }
""")

_TOC = ComponentDoc(
    tag="mj-toc",
    title="Table of Contents",
    group="navigation",
    summary="An in-page table of contents built from headings (or your own links) with scroll-spy.",
    description=(
        "<p><code>&lt;mj-toc&gt;</code> scans the headings inside <code>target</code> (an element id, or a CSS "
        "selector) and builds nested lists of links: by default <code>h2</code> and <code>h3</code> "
        "(<code>depth=\"2\"</code>), or whatever <code>heading-selector</code> matches. Headings without an id "
        "get a unique slug (letters and digits of any script). A MutationObserver rebuilds the list when the "
        "target's content changes; with no headings it shows &ldquo;No sections found&rdquo;.</p>"
        "<p>In manual mode, links you slot (<code>&lt;a href=\"#id\"&gt;</code>, or a list of them) replace "
        "the generated list and are tracked the same way.</p>"
        "<p>Scroll-spy marks the link of the last heading above the activation line (40% of the viewport "
        "height, or <code>offset</code> + 1 px if that is lower) with <code>aria-current=\"location\"</code> "
        "and emits <code>mj-toc-active-change</code>. A click emits the cancelable <code>mj-toc-navigate</code>, "
        "then scrolls the heading into view (<code>scroll-behavior</code>; instant under reduced motion), "
        "<code>offset</code> px below the top so it is not hidden under a sticky header, pushes the "
        "<code>#id</code> onto the history and focuses the heading.</p>"
    ),
    how_to_use=(
        "<p>Point <code>target</code> at the article and give the TOC a visible title with "
        "<code>heading</code> (the global <code>title</code> attribute also works but shows a tooltip over the "
        "whole component) or the <code>title</code> slot. Add <code>sticky</code> to keep it in view (top "
        "from <code>--mj-toc-sticky-top</code>) and set <code>offset</code> to the height of a sticky page "
        "header. Cancel <code>mj-toc-navigate</code> to handle the jump yourself.</p>"
        "<p>When the target is its own scroll box (as in these examples), make it reachable from the "
        "keyboard: <code>tabindex=\"0\"</code> and an <code>aria-label</code> on the scroller, so a "
        "keyboard user can scroll it with the arrow keys (WCAG 2.1.1).</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="target", description="Element whose headings are scanned: an id (with or without #) or a CSS selector.",
                     kind="string", values=["#guide", "main article"]),
        AttributeDoc(name="depth", description="Heading levels from h2: 1 = h2, 2 = h2-h3, 3 = h2-h4.", kind="number", default="2"),
        AttributeDoc(name="heading-selector", description="CSS selector for the headings; overrides depth.", kind="string",
                     values=["h2", "h2, h3, h4", "h2[id]"]),
        AttributeDoc(name="heading", description="Visible title above the list.", kind="string", values=["On this page", "Contents"]),
        AttributeDoc(name="sticky", description="position: sticky, scrolling itself when taller than the viewport.", kind="boolean"),
        AttributeDoc(name="offset", description="Height in px of a sticky header: the scroll-spy band starts below it and clicked headings land below it.",
                     kind="number", default="0"),
        AttributeDoc(name="scroll-behavior", description="Scrolling of a link click (reduced motion always jumps).", kind="enum",
                     values=["smooth", "instant", "auto"], default="smooth"),
        AttributeDoc(name="nav-label", description="Accessible name of the nav landmark.", kind="string", default="On this page"),
    ],
    events=[
        ("mj-toc-active-change", "The active section changed (scrolling, a rebuild or the first scan).",
         "{ id: string, element: Element | null, previousId: string }"),
        ("mj-toc-navigate", "Cancelable; a TOC link was clicked. Canceling skips the scroll, hash and focus.",
         "{ id: string, element: Element | null, originalEvent: MouseEvent }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>The TOC lists the guide's <code>h2</code> / <code>h3</code> headings. Scroll the guide and watch the active link (and <code>mj-toc-active-change</code>); click a link to jump.</p>",
            html=_block("""
                <div class="doc">
                  <mj-toc id="demo-toc" target="#guide" heading="On this page"></mj-toc>
                  <article id="guide" class="scroller" tabindex="0" aria-label="Guide">
                    <h2>Overview</h2>
                    <p>{filler}</p><p>{filler}</p>
                    <h2>Installation</h2>
                    <p>{filler}</p>
                    <h3>Requirements</h3>
                    <p>{filler}</p>
                    <h3>Install the package</h3>
                    <p>{filler}</p>
                    <h2>Configuration</h2>
                    <p>{filler}</p><p>{filler}</p>
                    <h2>Deployment</h2>
                    <p>{filler}</p><p>{filler}</p>
                  </article>
                </div>
            """).replace("{filler}", _FILLER),
            css=_TOC_CSS,
        ),
        ComponentExample(
            key="depth",
            title="Depth",
            description="<p>Two TOCs over one article: <code>depth=\"3\"</code> includes the <code>h4</code> headings, <code>depth=\"1\"</code> only the <code>h2</code>s.</p>",
            html=_block("""
                <div class="doc">
                  <mj-toc target="#api" depth="3" heading="All levels" nav-label="All levels"></mj-toc>
                  <mj-toc target="#api" depth="1" heading="Top level" nav-label="Top level"></mj-toc>
                  <article id="api" class="scroller" tabindex="0" aria-label="API reference">
                    <h2>Orders</h2><p>{filler}</p>
                    <h3>List orders</h3><p>{filler}</p>
                    <h4>Filtering</h4><p>{filler}</p>
                    <h4>Sorting</h4><p>{filler}</p>
                    <h3>Create an order</h3><p>{filler}</p>
                    <h2>Customers</h2><p>{filler}</p>
                    <h3>Merge customers</h3><p>{filler}</p>
                  </article>
                </div>
            """).replace("{filler}", _FILLER),
            css=_TOC_CSS + "mj-toc { --mj-toc-width: 170px; }\n",
        ),
        ComponentExample(
            key="manual",
            title="Your own links",
            description="<p>Slotted links (manual mode) replace the generated list and get the same scroll-spy; the <code>title</code> slot replaces the title.</p>",
            html=_block("""
                <div class="doc">
                  <mj-toc id="manual-toc" nav-label="Release notes">
                    <h3 slot="title" class="toc-title">Releases</h3>
                    <ul class="toc-links">
                      <li><a href="#v3">Version 3.0</a></li>
                      <li><a href="#v2-4">Version 2.4</a></li>
                      <li><a href="#v2-3">Version 2.3</a></li>
                    </ul>
                  </mj-toc>
                  <article class="scroller" tabindex="0" aria-label="Changelog">
                    <h2 id="v3">3.0 - New dashboard</h2><p>{filler}</p><p>{filler}</p>
                    <h2 id="v2-4">2.4 - Faster exports</h2><p>{filler}</p><p>{filler}</p>
                    <h2 id="v2-3">2.3 - Saved filters</h2><p>{filler}</p><p>{filler}</p>
                  </article>
                </div>
            """).replace("{filler}", _FILLER),
            css=_TOC_CSS + _block("""
                .toc-title { margin: 0 0 var(--mj-space-3); font-size: var(--mj-font-size-sm); }
                .toc-links { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--mj-space-1); }
                .toc-links a { display: block; padding: var(--mj-space-1) var(--mj-space-3); border-inline-start: 2px solid transparent; color: var(--mj-text-muted); text-decoration: none; }
                .toc-links a[aria-current="location"] { color: var(--mj-accent); border-inline-start-color: var(--mj-accent); }
            """),
        ),
        ComponentExample(
            key="sticky-offset",
            title="Sticky with offset",
            description="<p>The panel has a 48px sticky header. <code>sticky</code> keeps the TOC in view below it (<code>--mj-toc-sticky-top</code>) and <code>offset=\"56\"</code> lands clicked headings below the header.</p>",
            html=_block("""
                <div class="page scroller-page">
                  <header class="masthead">Developer docs</header>
                  <div class="doc">
                    <mj-toc target="#handbook" sticky offset="56" heading="Contents"></mj-toc>
                    <article id="handbook" class="flow">
                      <h2>Code review</h2><p>{filler}</p><p>{filler}</p>
                      <h2>Branching</h2><p>{filler}</p><p>{filler}</p>
                      <h2>Releases</h2><p>{filler}</p><p>{filler}</p>
                      <h2>On-call</h2><p>{filler}</p><p>{filler}</p>
                    </article>
                  </div>
                </div>
            """).replace("{filler}", _FILLER),
            css=_block("""
                .scroller-page { block-size: 320px; overflow: auto; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }
                .masthead { position: sticky; top: 0; z-index: 1; block-size: 48px; display: flex; align-items: center; padding-inline: var(--mj-space-4); background: var(--mj-surface); box-shadow: var(--mj-elevation-1); font-weight: var(--mj-font-weight-medium); }
                .doc { display: flex; gap: var(--mj-space-5); align-items: flex-start; padding: var(--mj-space-4); }
                .doc mj-toc { --mj-toc-sticky-top: 56px; }
                .flow { flex: 1; min-inline-size: 0; padding-block-end: 220px; }
                .flow p { color: var(--mj-text-muted); }
            """),
        ),
        ComponentExample(
            key="events",
            title="Dynamic content",
            description="<p>The article starts empty (&ldquo;No sections found&rdquo;). <em>Add section</em> appends a heading: the TOC rebuilds by itself. Clicks log <code>mj-toc-navigate</code>; the script cancels it for the first section to show the cancelable event.</p>",
            html=_block("""
                <p><button type="button" class="btn" id="add-section">Add section</button></p>
                <div class="doc">
                  <mj-toc id="live-toc" target="#live-article" heading="Sections"></mj-toc>
                  <article id="live-article" class="scroller" tabindex="0" aria-label="Sections"></article>
                </div>
            """),
            css=_TOC_CSS + _BTN_CSS,
            script=_block("""
                const article = document.getElementById("live-article")
                const toc = document.getElementById("live-toc")
                let count = 0
                document.getElementById("add-section").addEventListener("click", () => {
                  count = count + 1
                  const heading = document.createElement("h2")
                  heading.textContent = "Section " + count
                  const text = document.createElement("p")
                  text.textContent = "Added at " + new Date().toLocaleTimeString() + ". " + "Content of the new section. ".repeat(12)
                  article.append(heading, text)
                  mjSandbox.log("section added", { count: count })
                })
                toc.addEventListener("mj-toc-navigate", (event) => {
                  if (event.detail.id === "section-1") {
                    event.preventDefault()
                    mjSandbox.log("navigation canceled for the first section", { id: event.detail.id })
                  }
                })
            """),
        ),
    ],
    slots=[
        ("", "Manual mode: your own section links (anchors or a list of them); they replace the generated list.",
         '<ul><li><a href="#top">Back to the top</a></li></ul>'),
        ("title", "Replaces the generated title paragraph.", "<strong>Contents</strong>"),
    ],
    properties=[
        ("activeId", "string. Id of the active section (\"\" above the first heading) (read-only)."),
        ("sections", "{ id, text, level, element }[]. The tracked sections (read-only copy)."),
    ],
    parts=[
        ("title", "The generated title paragraph."),
        ("list", "The generated top-level list."),
        ("item", "Each generated list item."),
        ("anchor", "Each generated link."),
    ],
    css_properties=[
        ("--mj-toc-width", "Inline size (default 220px)."),
        ("--mj-toc-sticky-top", "Top inset with `sticky` (default var(--mj-app-bar-height, 0px))."),
        ("--mj-toc-indent", "Indent per nesting level (default var(--mj-space-4))."),
        ("--mj-toc-font-size", "Link font size (default var(--mj-font-size-sm))."),
        ("--mj-toc-link-color", "Link colour (default var(--mj-text-muted))."),
        ("--mj-toc-link-color-hover", "Hover colour (default var(--mj-text))."),
        ("--mj-toc-active-color", "Active link colour (default var(--mj-accent))."),
        ("--mj-toc-active-border", "Active link start border (default 2px solid var(--mj-accent))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-skip-link
# ---------------------------------------------------------------------------

_SKIP_PAGE_CSS = _block("""
    .site-header { display: flex; align-items: center; gap: var(--mj-space-5); padding: var(--mj-space-3) var(--mj-space-4); border-block-end: 1px solid var(--mj-border); }
    .site-header nav { display: flex; gap: var(--mj-space-4); }
    .site-header a { color: var(--mj-text); }
    main { padding: var(--mj-space-4); }
    main:focus, section:focus, footer:focus { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: 2px; }
""")

_SKIP_LINK = ComponentDoc(
    tag="mj-skip-link",
    title="Skip Link",
    group="navigation",
    summary="A skip-to-content link that appears on keyboard focus and moves focus past repeated blocks (WCAG 2.4.1).",
    description=(
        "<p><code>&lt;mj-skip-link&gt;</code> renders a native <code>&lt;a&gt;</code> that sits off-screen "
        "until it gets keyboard focus, then appears at the top start of the page. Activating it (Enter or "
        "click) emits the cancelable <code>mj-skip-link-activate</code> and moves focus to the target, making "
        "a non-focusable landmark temporarily focusable (<code>tabindex=\"-1\"</code>, removed on blur).</p>"
        "<p><code>target</code> is the destination id, written <code>#main</code> or <code>main</code>; any "
        "other value is tried as a CSS selector. The anchor always carries a fragment href "
        "(<code>#id</code>, or <code>#</code> when a selector match has no id) and the native jump is always "
        "suppressed, so the link never navigates to another document.</p>"
    ),
    how_to_use=(
        "<p>Make it the first focusable element of the page and point <code>target</code> at the main "
        "landmark. Change the text with <code>label</code> or by slotting content. Use "
        "<code>variant=\"inline\"</code> to keep it visible in the flow (a skip bar, or testing). Cancel "
        "<code>mj-skip-link-activate</code> to move focus yourself.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="target", description="Destination: an id (`#main` or `main`) or a CSS selector.", kind="string",
                     values=["#main-content", "main-content", "main"], default="#main"),
        AttributeDoc(name="label", description="Link text when nothing is slotted.", kind="string", values=["Skip to search results"],
                     default="Skip to main content"),
        AttributeDoc(name="variant", description="`inline` keeps the link visible in the flow; otherwise it shows only while focused.",
                     kind="enum", values=["default", "inline"], default="default"),
    ],
    events=[
        ("mj-skip-link-activate", "Cancelable; the link was activated. Canceling stops the focus move (the native jump is always suppressed).",
         "{ target: string, originalEvent: MouseEvent }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>Click inside the preview above the header, then press <kbd>Tab</kbd>: the skip link appears. Press <kbd>Enter</kbd> and focus jumps past the header links to the main content (outlined).</p>",
            html=_block("""
                <mj-skip-link id="demo-skip" target="#main-content"></mj-skip-link>
                <header class="site-header">
                  <strong>Northwind</strong>
                  <nav aria-label="Main">
                    <a href="#products">Products</a>
                    <a href="#pricing">Pricing</a>
                    <a href="#support">Support</a>
                    <a href="#contact">Contact</a>
                  </nav>
                </header>
                <main id="main-content">
                  <h1>Order history</h1>
                  <p>Keyboard users reach this content with one key press instead of tabbing through the header.</p>
                </main>
            """),
            css=_SKIP_PAGE_CSS,
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="inline",
            title="Inline, custom label",
            description="<p><code>variant=\"inline\"</code> keeps it visible; <code>label</code> sets the text and <code>target</code> is a bare id. Activate it: focus moves to the results.</p>",
            html=_block("""
                <mj-skip-link variant="inline" target="results" label="Skip to search results"></mj-skip-link>
                <form class="filters" aria-label="Filters">
                  <label>Colour <select><option>Any</option><option>Blue</option></select></label>
                  <label>Size <select><option>Any</option><option>M</option></select></label>
                  <label><input type="checkbox"> In stock</label>
                </form>
                <section id="results" aria-label="Results"><h2>24 results</h2><p>Blue widget, Green widget ...</p></section>
            """),
            css=_SKIP_PAGE_CSS + ".filters { display: flex; gap: var(--mj-space-4); padding: var(--mj-space-3) 0; }\n",
        ),
        ComponentExample(
            key="slots",
            title="Several targets, slotted labels",
            description="<p>A skip bar with three inline links: slotted markup as the label, a <code>#id</code> target and a CSS selector target (<code>.site-footer</code>).</p>",
            html=_block("""
                <div class="skip-bar">
                  <mj-skip-link variant="inline" target="#site-nav"><span>Skip to <strong>navigation</strong></span></mj-skip-link>
                  <mj-skip-link variant="inline" target="#content">Skip to content</mj-skip-link>
                  <mj-skip-link variant="inline" target=".site-footer">Skip to footer</mj-skip-link>
                </div>
                <nav id="site-nav" class="site-header" aria-label="Site"><a href="#a">Shop</a> <a href="#b">Journal</a></nav>
                <main id="content"><p>Main content.</p></main>
                <footer id="site-footer" class="site-footer"><p>Footer content.</p></footer>
            """),
            css=_SKIP_PAGE_CSS + ".skip-bar { display: flex; flex-wrap: wrap; gap: var(--mj-space-2); }\n",
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="events",
            title="Handling activation",
            description="<p>The script cancels <code>mj-skip-link-activate</code>, opens the collapsed filter panel and focuses its first field itself.</p>",
            html=_block("""
                <mj-skip-link id="skip-filters" variant="inline" target="#filters" label="Skip to filters"></mj-skip-link>
                <p>Long introduction text ...</p>
                <details id="filters">
                  <summary>Filters</summary>
                  <label>Category <select id="category"><option>All</option><option>Hardware</option></select></label>
                </details>
            """),
            css="details { margin-block-start: var(--mj-space-3); }\n",
            script=_block("""
                const skip = document.getElementById("skip-filters")
                skip.addEventListener("mj-skip-link-activate", (event) => {
                  event.preventDefault()
                  document.getElementById("filters").open = true
                  document.getElementById("category").focus()
                  mjSandbox.log("handled by the page", { target: event.detail.target })
                })
            """),
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description="<p>The <code>--mj-skip-link-*</code> custom properties and <code>::part(anchor)</code> restyle the link.</p>",
            html=_block("""
                <mj-skip-link variant="inline" target="#article" label="Jump to the article"></mj-skip-link>
                <main id="article"><p>Article text.</p></main>
            """),
            css=_block("""
                mj-skip-link {
                  --mj-skip-link-bg: var(--mj-text);
                  --mj-skip-link-color: var(--mj-surface);
                  --mj-skip-link-radius: var(--mj-radius-pill);
                  --mj-skip-link-padding: var(--mj-space-2) var(--mj-space-5);
                }
                mj-skip-link::part(anchor) { letter-spacing: 0.02em; }
                main:focus { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
            """),
        ),
    ],
    slots=[
        ("", "Link content; replaces the `label` text.", "<span>Skip to <strong>content</strong></span>"),
    ],
    properties=[
        ("anchorElement", "HTMLAnchorElement | null. The inner anchor (read-only)."),
    ],
    parts=[
        ("anchor", "The inner anchor."),
        ("label", "Wrapper of the label slot."),
    ],
    css_properties=[
        ("--mj-skip-link-bg", "Background (default var(--mj-accent))."),
        ("--mj-skip-link-color", "Text colour (default var(--mj-text-on-accent))."),
        ("--mj-skip-link-padding", "Padding (default var(--mj-space-3) var(--mj-space-5))."),
        ("--mj-skip-link-radius", "Corner radius (default var(--mj-radius-sm))."),
        ("--mj-skip-link-offset-top", "Top position when shown (default var(--mj-space-3))."),
        ("--mj-skip-link-offset-start", "Inline-start position when shown (default var(--mj-space-3))."),
        ("--mj-skip-link-z-index", "Stacking level (default var(--mj-layer-toast))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-footer-nav
# ---------------------------------------------------------------------------

_FOOTER_CSS = _block("""
    mj-footer-nav h3, mj-footer-nav [data-group-label] { margin: 0 0 var(--mj-space-3); font-size: var(--mj-font-size-sm); color: var(--mj-text); }
    mj-footer-nav ul { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--mj-space-2); }
    mj-footer-nav a { color: inherit; }
    mj-footer-nav .social { display: flex; gap: var(--mj-space-3); }
    mj-footer-nav .legal-links { display: flex; gap: var(--mj-space-4); }
""")

_FOOTER_GROUPS = _block("""
    <nav aria-labelledby="ft-product">
      <h3 id="ft-product">Product</h3>
      <ul><li><a href="#features">Features</a></li><li><a href="#pricing">Pricing</a></li><li><a href="#changelog">Changelog</a></li></ul>
    </nav>
    <nav aria-labelledby="ft-company">
      <h3 id="ft-company">Company</h3>
      <ul><li><a href="#about">About</a></li><li><a href="#careers">Careers</a></li><li><a href="#press">Press</a></li></ul>
    </nav>
    <nav aria-labelledby="ft-support">
      <h3 id="ft-support">Support</h3>
      <ul><li><a href="#help">Help centre</a></li><li><a href="#status">Status</a></li><li><a href="#contact">Contact</a></li></ul>
    </nav>
""")

_FOOTER_NAV = ComponentDoc(
    tag="mj-footer-nav",
    title="Footer Nav",
    group="navigation",
    summary="A site footer landmark with grouped link columns, brand and social areas and a legal bar.",
    description=(
        "<p><code>&lt;mj-footer-nav&gt;</code> renders a <code>&lt;footer role=\"contentinfo\"&gt;</code> with "
        "a brand area, a social area, a grid of link groups (the default slot) and a legal bar. Without "
        "<code>columns</code> the groups fill as many 160px-wide columns as fit; with it the count is fixed "
        "while the footer is wider than 560px and stacks below that.</p>"
        "<p><code>copyright=\"Acme Corp\"</code> renders &ldquo;&copy; 2026 Acme Corp&rdquo; in the legal bar "
        "(the year is the current one); a value that already contains &copy; is used as written.</p>"
        "<p>A click on any link in the footer (groups, brand, social, legal; also an <code>mj-link</code>) "
        "emits the cancelable <code>mj-footer-nav-navigate</code>; canceling prevents the navigation. Its "
        "<code>group</code> is the name of the default-slot group the link is in (empty elsewhere): the "
        "group's <code>label</code> attribute, else a <code>[data-group-label]</code> child, its "
        "<code>aria-label</code> / <code>aria-labelledby</code>, or its first heading or "
        "<code>&lt;strong&gt;</code>.</p>"
    ),
    how_to_use=(
        "<p>Write each group as a <code>&lt;nav aria-labelledby&gt;</code> with a heading and a list of links, "
        "so every navigation landmark has a name; style the lists yourself. <code>heading-level</code> "
        "(2-6) sets <code>aria-level</code> on the group headings to fit your page outline. "
        "<code>variant=\"dark\"</code> scopes the dark token palette to the footer (unless you set "
        "<code>theme</code>).</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="variant", description="`minimal` one column, `centered` centred text, `dark` the dark palette.", kind="enum",
                     values=["minimal", "centered", "dark"]),
        AttributeDoc(name="columns", description="Fixed column count (applies above 560px footer width). Absent: auto-fit.", kind="number"),
        AttributeDoc(name="copyright", description="Owner name; rendered as \"(c) <year> <name>\" unless it contains (c) itself.",
                     kind="string", values=["Acme Corp", "© 2020-2026 Acme Corp"]),
        AttributeDoc(name="heading-level", description="Outline level (2-6) applied as aria-level to each group heading.", kind="number"),
        AttributeDoc(name="nav-label", description="Accessible name of the footer landmark.", kind="string", default="Footer"),
    ],
    events=[
        ("mj-footer-nav-navigate", "Cancelable; a link in the footer was clicked. Canceling prevents the navigation.",
         "{ href: string, group: string, originalEvent: MouseEvent }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>Brand, social links, three labelled groups in three columns, legal links and the copyright. Clicking a link logs <code>mj-footer-nav-navigate</code> with its group.</p>",
            html=_block("""
                <mj-footer-nav id="demo-footer" copyright="Northwind Ltd" columns="3">
                  <strong slot="brand">Northwind</strong>
                  <div slot="social" class="social">
                    <a href="#social/mastodon">Mastodon</a>
                    <a href="#social/github">GitHub</a>
                  </div>
                """) + textwrap.indent(_FOOTER_GROUPS, "  ") + _block("""
                  <div slot="legal" class="legal-links">
                    <a href="#privacy">Privacy</a>
                    <a href="#terms">Terms</a>
                  </div>
                </mj-footer-nav>
            """),
            css=_FOOTER_CSS,
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="variants",
            title="Centered and minimal",
            description="<p><code>variant=\"centered\"</code> and <code>variant=\"minimal\"</code> (a single column).</p>",
            html=_block("""
                <div class="stack">
                  <mj-footer-nav variant="centered" copyright="Northwind Ltd" nav-label="Centered footer">
                    <strong slot="brand">Northwind</strong>
                    <nav aria-label="Legal"><ul class="legal-links"><li><a href="#privacy">Privacy</a></li><li><a href="#terms">Terms</a></li></ul></nav>
                  </mj-footer-nav>
                  <mj-footer-nav variant="minimal" copyright="Northwind Ltd" nav-label="Minimal footer">
                    <nav aria-label="Help"><ul><li><a href="#help">Help centre</a></li><li><a href="#contact">Contact</a></li></ul></nav>
                  </mj-footer-nav>
                </div>
            """),
            css=_FOOTER_CSS + ".stack { display: grid; gap: var(--mj-space-4); }\n.legal-links { justify-content: center; }\n",
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="dark",
            title="Dark variant, auto columns",
            description="<p><code>variant=\"dark\"</code> uses the dark palette whatever the page theme. Without <code>columns</code> the five groups auto-fit (narrow the window to see them wrap).</p>",
            html=_block("""
                <mj-footer-nav variant="dark" copyright="© 2019-2026 Northwind Ltd">
                  <strong slot="brand">Northwind</strong>
                """) + textwrap.indent(_FOOTER_GROUPS, "  ") + _block("""
                  <nav aria-labelledby="ft-dev"><h3 id="ft-dev">Developers</h3><ul><li><a href="#api">API</a></li><li><a href="#sdk">SDKs</a></li></ul></nav>
                  <nav aria-labelledby="ft-legal"><h3 id="ft-legal">Legal</h3><ul><li><a href="#privacy">Privacy</a></li><li><a href="#terms">Terms</a></li></ul></nav>
                </mj-footer-nav>
            """),
            css=_FOOTER_CSS,
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="events",
            title="Analytics routing",
            description="<p>The script cancels <code>mj-footer-nav-navigate</code> and reports the group. Groups are named three ways: a <code>label</code> attribute, a <code>[data-group-label]</code> child and a heading. <code>heading-level=\"2\"</code> sets <code>aria-level</code> on the headings.</p>",
            html=_block("""
                <mj-footer-nav id="tracked-footer" heading-level="2" copyright="Northwind Ltd">
                  <nav label="Shop" aria-label="Shop"><ul><li><a href="#new">New in</a></li><li><a href="#sale">Sale</a></li></ul></nav>
                  <nav aria-label="Service"><p data-group-label>Service</p><ul><li><a href="#returns">Returns</a></li><li><a href="#delivery">Delivery</a></li></ul></nav>
                  <nav aria-labelledby="ft-about"><h3 id="ft-about">About</h3><ul><li><a href="#story">Our story</a></li></ul></nav>
                  <a slot="legal" href="#imprint">Imprint</a>
                </mj-footer-nav>
                <p>Last click: <output id="footer-click">none</output></p>
            """),
            css=_FOOTER_CSS,
            script=_block("""
                const footer = document.getElementById("tracked-footer")
                const output = document.getElementById("footer-click")
                footer.addEventListener("mj-footer-nav-navigate", (event) => {
                  event.preventDefault()
                  output.textContent = (event.detail.group || "(no group)") + " -> " + event.detail.href
                  mjSandbox.log("tracked", { group: event.detail.group, href: event.detail.href })
                })
            """),
        ),
    ],
    slots=[
        ("brand", "Logo or company name above the groups.", "<strong>Acme</strong>"),
        ("", "Link groups, one element each (a named nav with a heading and a list).",
         '<nav aria-label="More"><strong>More</strong><ul><li><a href="#more">More links</a></li></ul></nav>'),
        ("social", "Social links above the groups.", '<a href="#social">Follow us</a>'),
        ("legal", "Legal links in the bottom bar, after the copyright.", '<a href="#cookies">Cookie settings</a>'),
    ],
    properties=[
        ("groups", "Element[]. The default-slot group elements (read-only)."),
    ],
    parts=[
        ("root", "The centred content wrapper."),
        ("brand", "Brand area."),
        ("social", "Social area."),
        ("columns", "The grid of groups."),
        ("group", "Wrapper of the group slot (display: contents)."),
        ("legal", "The bottom bar with copyright and legal slot."),
    ],
    css_properties=[
        ("--mj-footer-nav-bg", "Background (default var(--mj-bg-subtle))."),
        ("--mj-footer-nav-color", "Text colour (default var(--mj-text-muted))."),
        ("--mj-footer-nav-padding", "Padding (default var(--mj-space-8) var(--mj-space-6))."),
        ("--mj-footer-nav-columns-gap", "Gap between groups (default var(--mj-space-8))."),
        ("--mj-footer-nav-legal-border", "Border above the legal bar (default 1px solid var(--mj-border))."),
        ("--mj-footer-nav-legal-font-size", "Legal bar font size (default var(--mj-font-size-xs))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-menu
# ---------------------------------------------------------------------------

_MENU_CSS = _block("""
    .trigger { min-block-size: var(--mj-control-height-md); padding-inline: var(--mj-space-4); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-md); background: var(--mj-surface); color: var(--mj-text); font: inherit; cursor: pointer; }
""")

_MENU_TOGGLE = _block("""
    // mj-menu does not listen to its trigger: the page toggles `open`.
    for (const menu of document.querySelectorAll("mj-menu[anchor]")) {
      const trigger = document.getElementById(menu.getAttribute("anchor"))
      if (trigger !== null && trigger.matches("button")) {
        trigger.addEventListener("click", () => { menu.open = !menu.open })
      }
    }
""")

_MENU = ComponentDoc(
    tag="mj-menu",
    title="Menu",
    group="navigation",
    summary="A WAI-ARIA menu popup anchored to a trigger, with checkable items, keyboard navigation and typeahead.",
    description=(
        "<p><code>&lt;mj-menu&gt;</code> is a <code>role=\"menu\"</code> popup positioned against its trigger "
        "(<code>anchor</code>, with <code>placement</code>; it flips when there is no room). Items are the "
        "slotted elements with role <code>menuitem</code>, <code>menuitemcheckbox</code> or "
        "<code>menuitemradio</code>, <code>class=\"item\"</code> or <code>data-menu-item</code> (an item "
        "without a role becomes a <code>menuitem</code>), including items nested in slotted wrappers. "
        "<code>&lt;hr&gt;</code> / <code>role=\"separator\"</code> draw dividers and "
        "<code>role=\"presentation\"</code> elements are group captions. Items, dividers and captions inside "
        "a slotted wrapper such as a <code>role=\"group\"</code> get the same styles as direct children. A "
        "menu without items shows a \"No options\" notice.</p>"
        "<p>Opening moves real focus to the first enabled item (roving focus, not "
        "<code>aria-activedescendant</code>) and sets <code>aria-expanded</code> on the trigger. ArrowDown / "
        "ArrowUp (wrapping), Home and End move; a printable key jumps to the next item starting with it; "
        "Enter, Space or a click activates; Escape, Tab or a press outside closes and focus returns to the "
        "trigger. <code>aria-disabled=\"true\"</code> items are skipped and cannot be chosen.</p>"
        "<p>Choosing an item emits the cancelable <code>mj-menu-select</code> first, with the checked state "
        "the item is about to get. Unless it is canceled, a checkbox item then toggles, a radio item is checked "
        "(unchecking the other radios of its <code>role=\"group\"</code>, or of the menu) and the menu closes "
        "(not with <code>close-on-select=\"false\"</code>). Canceling leaves the checked state and the menu "
        "as they were. Only the dropdown variant is implemented; <code>variant=\"mega\"</code> only widens "
        "the popup.</p>"
    ),
    how_to_use=(
        "<p>Give the trigger an id, <code>aria-haspopup=\"menu\"</code> and <code>aria-expanded=\"false\"</code>, "
        "and set <code>anchor</code> to that id. The menu does not listen to its trigger: toggle "
        "<code>menu.open</code> (or call <code>show()</code> / <code>hide()</code>) in the trigger's click "
        "handler. Give items a <code>value</code> attribute to get it in <code>mj-menu-select</code> (else the "
        "item text). Wrap each set of radio items in a <code>role=\"group\"</code> (named with "
        "<code>aria-labelledby</code> or <code>aria-label</code>) so they check independently.</p>"
        "<p><code>mj-menu-open</code> and <code>mj-menu-close</code> are cancelable and fire before the change; "
        "each close fires once with its reason.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="open", description="Shows the menu (and focuses its first item).", kind="boolean"),
        AttributeDoc(name="anchor", description="The trigger: an element id (looked up first) or a CSS selector.", kind="string",
                     values=["file-menu-trigger"]),
        AttributeDoc(name="placement", description="Preferred side and alignment against the trigger; flips when there is no room.",
                     kind="enum", values=["top", "top-start", "top-end", "bottom", "bottom-start", "bottom-end",
                                          "start", "start-top", "start-bottom", "end", "end-top", "end-bottom"],
                     default="bottom-start"),
        AttributeDoc(name="label", description="Accessible name of the menu; defaults to the trigger's name.", kind="string"),
        AttributeDoc(name="variant", description="`dropdown` (the only behaviour); `mega` widens the popup to 480px.", kind="enum",
                     values=["dropdown", "mega"], default="dropdown"),
        AttributeDoc(name="close-on-select", description="Close after an item is chosen; uncheck (`false`) to keep it open.",
                     kind="boolean", default="true"),
    ],
    events=[
        ("mj-menu-open", "Cancelable; the menu is about to open. Canceling removes `open` again.", "{ trigger: Element | null }"),
        ("mj-menu-close", "Cancelable; the menu is about to close (once per close).",
         "{ reason: 'select' | 'escape' | 'blur' | 'external' }"),
        ("mj-menu-select", "Cancelable; an item was chosen. Fires before a checkbox / radio item changes; canceling keeps its checked state and keeps the menu open.",
         "{ item: Element, value: string, checked: boolean | null }  (the state the item gets)"),
        ("mj-menu-item-focus", "Another item became the active (focused or hovered) item.", "{ item: Element }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>The button toggles <code>open</code>. Choose with the mouse or the keys (arrows, Home, End, a letter, Enter); Delete is disabled. The chosen <code>value</code> is shown below.</p>",
            html=_block("""
                <button type="button" id="file-menu-trigger" class="trigger" aria-haspopup="menu" aria-expanded="false">File</button>
                <mj-menu id="file-menu" anchor="file-menu-trigger">
                  <div role="menuitem" value="new">New document</div>
                  <div role="menuitem" value="open">Open...</div>
                  <div role="menuitem" value="duplicate">Duplicate</div>
                  <hr>
                  <div role="menuitem" value="delete" aria-disabled="true">Delete</div>
                </mj-menu>
                <p>Last action: <output id="file-menu-result">none</output></p>
            """),
            css=_MENU_CSS,
            script=_MENU_TOGGLE + _block("""
                const result = document.getElementById("file-menu-result")
                const fileMenu = document.getElementById("file-menu")
                if (result !== null && fileMenu !== null) {
                  fileMenu.addEventListener("mj-menu-select", (event) => { result.textContent = event.detail.value })
                }
            """),
            height=280,
        ),
        ComponentExample(
            key="checkable",
            title="Checkbox and radio items",
            description="<p><code>menuitemcheckbox</code> items toggle, <code>menuitemradio</code> items check one of the group; <code>close-on-select=\"false\"</code> keeps the menu open. Watch <code>checked</code> in <code>mj-menu-select</code>.</p>",
            html=_block("""
                <button type="button" id="view-trigger" class="trigger" aria-haspopup="menu" aria-expanded="false">View</button>
                <mj-menu anchor="view-trigger" close-on-select="false" label="View options">
                  <div role="presentation">Panels</div>
                  <div role="menuitemcheckbox" aria-checked="true" value="sidebar">Sidebar</div>
                  <div role="menuitemcheckbox" aria-checked="false" value="minimap">Minimap</div>
                  <hr>
                  <div role="presentation">Density</div>
                  <div role="menuitemradio" aria-checked="false" value="compact">Compact</div>
                  <div role="menuitemradio" aria-checked="true" value="comfortable">Comfortable</div>
                  <div role="menuitemradio" aria-checked="false" value="spacious">Spacious</div>
                </mj-menu>
            """),
            css=_MENU_CSS,
            script=_MENU_TOGGLE,
            height=380,
        ),
        ComponentExample(
            key="groups",
            title="Grouped items",
            description="<p>Two <code>role=\"group\"</code> wrappers hold independent radio sets; their items, captions and dividers are styled like direct children. Tick <em>Lock choices</em>: the script cancels <code>mj-menu-select</code>, so the chosen item keeps its checked state.</p>",
            html=_block("""
                <p class="row">
                  <button type="button" id="sort-trigger" class="trigger" aria-haspopup="menu" aria-expanded="false">Sort and group</button>
                  <label><input type="checkbox" id="lock-choices"> Lock choices</label>
                </p>
                <mj-menu id="sort-menu" anchor="sort-trigger" close-on-select="false" label="Sort and group">
                  <div role="group" aria-labelledby="sort-caption">
                    <div role="presentation" id="sort-caption">Sort by</div>
                    <div role="menuitemradio" aria-checked="true" value="name">Name</div>
                    <div role="menuitemradio" aria-checked="false" value="modified">Last modified</div>
                    <div role="menuitemradio" aria-checked="false" value="size">Size</div>
                  </div>
                  <hr>
                  <div role="group" aria-labelledby="group-caption">
                    <div role="presentation" id="group-caption">Group by</div>
                    <div role="menuitemradio" aria-checked="false" value="none">None</div>
                    <div role="menuitemradio" aria-checked="true" value="type">Type</div>
                  </div>
                  <hr>
                  <div role="menuitemcheckbox" aria-checked="true" value="folders-first">Folders first</div>
                </mj-menu>
            """),
            css=_MENU_CSS + ".row { display: flex; align-items: center; gap: var(--mj-space-4); }\n",
            script=_MENU_TOGGLE + _block("""
                const sortMenu = document.getElementById("sort-menu")
                sortMenu.addEventListener("mj-menu-select", (event) => {
                  if (document.getElementById("lock-choices").checked) {
                    event.preventDefault()
                    mjSandbox.log("selection canceled, checked state kept", { value: event.detail.value })
                  }
                })
            """),
            height=420,
        ),
        ComponentExample(
            key="placement",
            title="Placement",
            description="<p><code>placement=\"end-top\"</code> opens beside the trigger, <code>bottom-end</code> aligns to the trigger's end edge.</p>",
            html=_block("""
                <div class="row">
                  <button type="button" id="share-trigger" class="trigger" aria-haspopup="menu" aria-expanded="false">Share</button>
                  <mj-menu anchor="share-trigger" placement="end-top">
                    <div role="menuitem">Copy link</div>
                    <div role="menuitem">E-mail</div>
                    <div role="menuitem">Embed</div>
                  </mj-menu>
                  <button type="button" id="account-trigger" class="trigger" aria-haspopup="menu" aria-expanded="false">Account</button>
                  <mj-menu anchor="account-trigger" placement="bottom-end">
                    <div role="menuitem">Profile</div>
                    <div role="menuitem">Billing</div>
                    <div role="menuitem">Sign out</div>
                  </mj-menu>
                </div>
            """),
            css=_MENU_CSS + ".row { display: flex; justify-content: space-between; }\n",
            script=_MENU_TOGGLE,
            height=240,
        ),
        ComponentExample(
            key="keyboard",
            title="Typeahead and long lists",
            description="<p>Open the menu and type a letter (e.g. <kbd>p</kbd> repeatedly) to jump between items; the list scrolls inside <code>--mj-menu-max-height</code>. Items use <code>data-menu-item</code> instead of a role.</p>",
            html=_block("""
                <button type="button" id="country-trigger" class="trigger" aria-haspopup="menu" aria-expanded="false">Country</button>
                <mj-menu anchor="country-trigger" label="Country">
                  <div data-menu-item>Austria</div><div data-menu-item>Belgium</div><div data-menu-item>Denmark</div>
                  <div data-menu-item>Finland</div><div data-menu-item>France</div><div data-menu-item>Germany</div>
                  <div data-menu-item>Ireland</div><div data-menu-item>Italy</div><div data-menu-item>Norway</div>
                  <div data-menu-item>Poland</div><div data-menu-item>Portugal</div><div data-menu-item>Spain</div>
                  <div data-menu-item>Sweden</div>
                </mj-menu>
            """),
            css=_MENU_CSS + "mj-menu { --mj-menu-max-height: 220px; }\n",
            script=_MENU_TOGGLE,
            height=300,
        ),
        ComponentExample(
            key="events",
            title="Canceling open and close",
            description="<p>While <em>Read-only</em> is ticked the script cancels <code>mj-menu-open</code>. While <em>Pin open</em> is ticked it cancels every <code>mj-menu-close</code> except one after a selection. The buttons call <code>show()</code> and <code>hide()</code>.</p>",
            html=_block("""
                <p class="row">
                  <button type="button" id="edit-trigger" class="trigger" aria-haspopup="menu" aria-expanded="false">Edit</button>
                  <label><input type="checkbox" id="read-only"> Read-only</label>
                  <label><input type="checkbox" id="pin-open"> Pin open</label>
                  <button type="button" class="btn" id="menu-show">show()</button>
                  <button type="button" class="btn" id="menu-hide">hide()</button>
                </p>
                <mj-menu id="edit-menu" anchor="edit-trigger">
                  <div role="menuitem">Undo</div>
                  <div role="menuitem">Redo</div>
                  <div role="menuitem">Select all</div>
                </mj-menu>
            """),
            css=_MENU_CSS + _BTN_CSS + ".row { display: flex; flex-wrap: wrap; align-items: center; gap: var(--mj-space-3); }\n",
            script=_MENU_TOGGLE + _block("""
                const menu = document.getElementById("edit-menu")
                menu.addEventListener("mj-menu-open", (event) => {
                  if (document.getElementById("read-only").checked) {
                    event.preventDefault()
                    mjSandbox.log("open canceled: read-only", {})
                  }
                })
                menu.addEventListener("mj-menu-close", (event) => {
                  if (document.getElementById("pin-open").checked && event.detail.reason !== "select") {
                    event.preventDefault()
                    mjSandbox.log("close canceled", event.detail)
                  }
                })
                document.getElementById("menu-show").addEventListener("click", () => menu.show())
                document.getElementById("menu-hide").addEventListener("click", () => menu.hide())
            """),
            height=260,
        ),
    ],
    slots=[
        ("", "Menu items (role menuitem / menuitemcheckbox / menuitemradio, class item or data-menu-item), separators and captions.",
         '<div role="menuitem" value="rename">Rename</div>'),
    ],
    properties=[
        ("open", "boolean. Reflects the `open` attribute."),
        ("items", "Element[]. The enabled items in order (read-only)."),
        ("activeItem", "Element | null. The highlighted item (read-only)."),
        ("triggerElement", "Element | null. The resolved trigger; set an element to use it instead of `anchor`."),
    ],
    methods=[
        ("show()", "Opens the menu (same as setting `open`)."),
        ("hide()", "Closes the menu with reason `external`."),
    ],
    parts=[
        ("menu", "The popup (role menu)."),
        ("empty-notice", "The \"No options\" notice shown when there are no items."),
    ],
    css_properties=[
        ("--mj-menu-min-width", "Minimum width (default 160px)."),
        ("--mj-menu-max-height", "Maximum height before the list scrolls (default 360px)."),
        ("--mj-menu-bg", "Background (default var(--mj-surface))."),
        ("--mj-menu-radius", "Corner radius (default var(--mj-radius-md))."),
        ("--mj-menu-shadow", "Shadow (default var(--mj-elevation-3))."),
        ("--mj-menu-item-height", "Minimum item height (default 40px)."),
        ("--mj-menu-item-padding", "Item padding (default 0 var(--mj-space-4))."),
        ("--mj-menu-item-focus-bg", "Active item background (default var(--mj-bg-muted))."),
        ("--mj-menu-z-index", "Stacking level (default var(--mj-layer-popover))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-tree-nav
# ---------------------------------------------------------------------------

_TREE_NAV = ComponentDoc(
    tag="mj-tree-nav",
    title="Tree Nav",
    group="navigation",
    summary="A hierarchical navigation tree (WAI-ARIA tree) with expand / collapse, current-page marking and remembered state.",
    description=(
        "<p><code>&lt;mj-tree-nav&gt;</code> turns nested lists into a <code>role=\"tree\"</code> inside a nav "
        "landmark. Each <code>&lt;li&gt;</code> becomes a <code>treeitem</code> (level, set size and position "
        "are filled in); its content is wrapped in a <code>.item-row</code> and an item with a child "
        "<code>&lt;ul&gt;</code> gets a chevron button and <code>aria-expanded</code> (collapsed unless you "
        "write <code>aria-expanded=\"true\"</code>). The item styles are adopted into the document, scoped to "
        "<code>mj-tree-nav</code>, and use the light-DOM classes <code>.item-row</code>, "
        "<code>.item-link</code>, <code>.toggle-btn</code> and <code>.child-tree</code>.</p>"
        "<p>Keyboard focus is real focus on the items with one roving tab stop: ArrowDown / ArrowUp, Home, End, "
        "ArrowRight (expand, then to the first child), ArrowLeft (collapse, then to the parent; mirrored in "
        "RTL), Enter follows the link, Space toggles, <code>*</code> expands all siblings and a letter jumps "
        "by typeahead.</p>"
        "<p><code>current</code> (an item id, a link <code>href</code> or a link id) marks that item "
        "<code>aria-current=\"page\"</code> and, unless <code>auto-expand=\"false\"</code>, expands its "
        "ancestors. With <code>persist-state</code> the expanded branches are saved in "
        "<code>sessionStorage</code> and restored on the next load.</p>"
    ),
    how_to_use=(
        "<p>Put <code>&lt;li&gt;</code> elements, each with a link, directly in the component and nest a "
        "<code>&lt;ul&gt;</code> for a branch. Set <code>current</code> to the current page's href. A click on a "
        "link emits the cancelable <code>mj-tree-nav-navigate</code> (cancel it to route client-side); with "
        "<code>parent-toggle</code> a parent's label toggles its branch instead of navigating. Expanding and "
        "collapsing emit the cancelable <code>mj-tree-nav-expand</code> / <code>mj-tree-nav-collapse</code>.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="current", description="The current page: an item id, a link href or a link id.", kind="string",
                     values=["#guides/deploy", "#reference/rest", "#overview"]),
        AttributeDoc(name="auto-expand", description="Expand the ancestors of the current item; uncheck (`false`) to leave them.",
                     kind="boolean", default="true"),
        AttributeDoc(name="parent-toggle", description="A parent's label toggles its branch instead of following its link.", kind="boolean"),
        AttributeDoc(name="compact", description="Shorter rows (28px).", kind="boolean"),
        AttributeDoc(name="persist-state", description="Save expanded branches in sessionStorage and restore them on load.", kind="boolean"),
        AttributeDoc(name="persist-key", description="sessionStorage key for the saved state.", kind="string", default="mj-tree-nav"),
        AttributeDoc(name="nav-label", description="Accessible name of the nav landmark and the tree.", kind="string", default="Navigation"),
    ],
    events=[
        ("mj-tree-nav-navigate", "Cancelable; an item link was activated (click or Enter). Canceling prevents the navigation.",
         "{ item: Element, href: string }"),
        ("mj-tree-nav-expand", "Cancelable; a branch is about to expand.", "{ item: Element, id: string }"),
        ("mj-tree-nav-collapse", "Cancelable; a branch is about to collapse.", "{ item: Element, id: string }"),
        ("mj-tree-nav-focus", "The roving tab stop moved to another item.", "{ item: Element }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p><code>current</code> marks Deployment and expands Guides. Click a link: the script plays the router (cancels <code>mj-tree-nav-navigate</code> and moves <code>current</code>). Use the arrow keys, Space and Enter.</p>",
            html=_block("""
                <mj-tree-nav id="docs-tree" nav-label="Documentation" current="#guides/deploy">
                  <li><a href="#overview">Overview</a></li>
                  <li>
                    <a href="#guides">Guides</a>
                    <ul>
                      <li><a href="#guides/install">Installation</a></li>
                      <li><a href="#guides/deploy">Deployment</a></li>
                      <li><a href="#guides/upgrade">Upgrading</a></li>
                    </ul>
                  </li>
                  <li>
                    <a href="#reference">API reference</a>
                    <ul>
                      <li><a href="#reference/rest">REST endpoints</a></li>
                      <li><a href="#reference/events">Webhooks</a></li>
                    </ul>
                  </li>
                  <li><a href="#changelog">Changelog</a></li>
                </mj-tree-nav>
            """),
            css="mj-tree-nav { max-inline-size: 280px; }\n",
            script=_LINK_GUARD + _block("""
                const tree = document.getElementById("docs-tree")
                if (tree !== null) {
                  tree.addEventListener("mj-tree-nav-navigate", (event) => {
                    event.preventDefault()
                    tree.setAttribute("current", event.detail.href)
                  })
                }
            """),
        ),
        ComponentExample(
            key="compact",
            title="Compact, deep and pre-expanded",
            description="<p><code>compact</code> rows, three levels, and a branch written with <code>aria-expanded=\"true\"</code> so it starts open. Press <kbd>*</kbd> on a top-level item to expand all its siblings.</p>",
            html=_block("""
                <mj-tree-nav compact nav-label="Files">
                  <li aria-expanded="true">
                    <a href="#src">src</a>
                    <ul>
                      <li>
                        <a href="#src/components">components</a>
                        <ul><li><a href="#src/components/button">button.js</a></li><li><a href="#src/components/menu">menu.js</a></li></ul>
                      </li>
                      <li><a href="#src/index">index.js</a></li>
                    </ul>
                  </li>
                  <li>
                    <a href="#tests">tests</a>
                    <ul><li><a href="#tests/button">button.test.js</a></li></ul>
                  </li>
                  <li><a href="#readme">README.md</a></li>
                </mj-tree-nav>
            """),
            css="mj-tree-nav { max-inline-size: 280px; }\n",
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="parent-toggle",
            title="Parent labels toggle",
            description="<p>With <code>parent-toggle</code> a click on a parent's label opens or closes the branch instead of navigating; leaf links still navigate.</p>",
            html=_block("""
                <mj-tree-nav parent-toggle nav-label="Settings">
                  <li>
                    <a href="#account">Account</a>
                    <ul><li><a href="#account/profile">Profile</a></li><li><a href="#account/security">Security</a></li></ul>
                  </li>
                  <li>
                    <a href="#workspace">Workspace</a>
                    <ul><li><a href="#workspace/members">Members</a></li><li><a href="#workspace/billing">Billing</a></li></ul>
                  </li>
                </mj-tree-nav>
            """),
            css="mj-tree-nav { max-inline-size: 280px; }\n",
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="persist-state",
            title="Remembered branches",
            description="<p><code>persist-state</code> with a <code>persist-key</code>: expand or collapse branches, then press Run. The branches come back as you left them (sessionStorage).</p>",
            html=_block("""
                <mj-tree-nav id="persisted-tree" persist-state persist-key="catalog-demo-tree" nav-label="Handbook">
                  <li id="hb-people">
                    <a href="#people">People</a>
                    <ul><li><a href="#people/onboarding">Onboarding</a></li><li><a href="#people/leave">Leave</a></li></ul>
                  </li>
                  <li id="hb-engineering">
                    <a href="#engineering">Engineering</a>
                    <ul><li><a href="#engineering/reviews">Code review</a></li><li><a href="#engineering/oncall">On-call</a></li></ul>
                  </li>
                  <li id="hb-finance">
                    <a href="#finance">Finance</a>
                    <ul><li><a href="#finance/expenses">Expenses</a></li></ul>
                  </li>
                </mj-tree-nav>
            """),
            css="mj-tree-nav { max-inline-size: 280px; }\n",
            script=_LINK_GUARD,
        ),
        ComponentExample(
            key="events",
            title="Canceling a collapse",
            description="<p>The Pinned branch cannot be collapsed: the script cancels its <code>mj-tree-nav-collapse</code>. Every expand, collapse, focus move and navigation shows in the Events panel.</p>",
            html=_block("""
                <mj-tree-nav id="pinned-tree" nav-label="Boards" current="#pinned/roadmap">
                  <li id="pinned">
                    <a href="#pinned">Pinned</a>
                    <ul><li><a href="#pinned/roadmap">Roadmap</a></li><li><a href="#pinned/bugs">Bugs</a></li></ul>
                  </li>
                  <li>
                    <a href="#archive">Archive</a>
                    <ul><li><a href="#archive/2025">2025</a></li><li><a href="#archive/2024">2024</a></li></ul>
                  </li>
                </mj-tree-nav>
            """),
            css="mj-tree-nav { max-inline-size: 280px; }\n",
            script=_LINK_GUARD + _block("""
                const tree = document.getElementById("pinned-tree")
                tree.addEventListener("mj-tree-nav-collapse", (event) => {
                  if (event.detail.id === "pinned") {
                    event.preventDefault()
                    mjSandbox.log("collapse canceled: branch is pinned", { id: event.detail.id })
                  }
                })
            """),
        ),
    ],
    slots=[
        ("", "Tree items: <li> elements with a link; nest a <ul> of <li> for a branch.", '<li><a href="#new">New page</a></li>'),
    ],
    properties=[
        ("currentItem", "Element | null. The item marked aria-current=\"page\" (read-only)."),
        ("expandedItems", "Element[]. Items whose branch is expanded (read-only)."),
        ("activeItem", "Element | null. The item holding the roving tab stop (read-only)."),
    ],
    parts=[
        ("tree", "The tree list in the shadow root (the items are light DOM: style `.item-row`, `.item-link`, `.toggle-btn`, `.child-tree`)."),
    ],
    css_properties=[
        ("--mj-tree-nav-font-size", "Font size (default var(--mj-font-size-sm))."),
        ("--mj-tree-nav-item-height", "Row height (default 36px)."),
        ("--mj-tree-nav-item-height-compact", "Row height with `compact` (default 28px)."),
        ("--mj-tree-nav-indent", "Indent of a child level (default var(--mj-space-5))."),
        ("--mj-tree-nav-toggle-size", "Chevron button size (default 20px)."),
        ("--mj-tree-nav-bg-hover", "Row hover / focus background (default var(--mj-bg-muted))."),
        ("--mj-tree-nav-bg-active", "Current row background (default var(--mj-bg-muted))."),
        ("--mj-tree-nav-active-border-width", "Current row marker width (default 2px)."),
        ("--mj-tree-nav-active-border-color", "Current row marker colour (default var(--mj-accent))."),
        ("--mj-tree-nav-color-active", "Current link colour (default var(--mj-accent))."),
        ("--mj-tree-nav-transition-duration", "Chevron rotation duration (default var(--mj-motion-fast))."),
    ],
)


COMPONENTS = [
    _LINK,
    _APP_BAR,
    _SIDE_NAV,
    _BREADCRUMB,
    _TABS,
    _NAV_STEPPER,
    _WIZARD,
    _PAGINATION,
    _TOC,
    _SKIP_LINK,
    _FOOTER_NAV,
    _MENU,
    _TREE_NAV,
]
