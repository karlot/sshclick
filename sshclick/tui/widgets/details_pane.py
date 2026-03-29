from textual.app import ComposeResult
from rich.box import MINIMAL
from rich.console import Group as RichGroup
from rich.rule import Rule
from rich.table import Table

from textual.containers import Grid, Vertical
from textual.widgets import ContentSwitcher, Static, TabbedContent, TabPane

from sshclick.core import SSH_Config, SSH_Group, SSH_Host, generate_graph
from sshclick.tui.state import SSHNode


class DetailsPane(Vertical):
    """Right-hand inspector that renders group and host details."""

    def __init__(self, sshconf: SSH_Config, id: str | None = None) -> None:
        self.sshconf = sshconf
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        # We keep the group and host states mounted and switch between them so
        # tab state and widget structure stay stable while the selection changes.
        with ContentSwitcher(initial="details_group_view", id="details_switcher"):
            with Vertical(id="details_group_view", classes="details_view"):
                with Grid(id="group_overview_top", classes="details_split_row"):
                    yield Static(id="group_summary_card", classes="details_card details_card_narrow")
                    yield Static(id="group_info_card", classes="details_card")
                yield Static(id="group_hosts_card", classes="details_card")

            with Vertical(id="details_host_view", classes="details_view"):
                with TabbedContent(initial="host_overview_tab", id="host_tabs"):
                    with TabPane("Overview", id="host_overview_tab"):
                        with Vertical(classes="details_tab_scroll"):
                            with Grid(id="host_overview_top", classes="details_split_row"):
                                yield Static(id="host_identity_card", classes="details_card")
                                yield Static(id="host_connection_card", classes="details_card")
                            yield Static(id="host_info_card", classes="details_card")
                            yield Static(id="host_params_card", classes="details_card")
                    with TabPane("Connectivity", id="host_connectivity_tab"):
                        with Vertical(classes="details_tab_scroll"):
                            with Grid(id="host_connectivity_top", classes="details_split_row"):
                                yield Static(id="host_connectivity_route_card", classes="details_card")
                                yield Static(id="host_connectivity_tunnels_card", classes="details_card")
                            yield Static(id="host_connectivity_graph_card", classes="details_card")

    def on_mount(self) -> None:
        self._set_card_titles()
        self._show_empty_state()
        self.call_after_refresh(self._sync_scrollbar_visibility)

    def on_resize(self, _event) -> None:
        self.call_after_refresh(self._sync_scrollbar_visibility)

    def update_config(self, sshconf: SSH_Config) -> None:
        """Replace the backing config model after a reload."""

        self.sshconf = sshconf

    def show_host_tab(self, tab_id: str) -> None:
        """Switch the active host tab when the details pane is showing a host."""

        if self._switcher().display is False:
            return
        if self._switcher().current != "details_host_view":
            return

        self.query_one("#host_tabs", TabbedContent).active = tab_id

    def update_node(self, node: SSHNode) -> None:
        """Refresh the inspector for the currently selected group or host."""

        if node is None:
            self._show_empty_state()
            return

        if isinstance(node, SSH_Group):
            self._show_group(node)
            return

        self._show_host(node)

    def _build_group_overview(self, group: SSH_Group):
        """Render the compact summary card shown for a selected group."""

        return RichGroup(
            self._detail_grid([("Name", group.name)]),
            self._inner_rule(),
            self._detail_grid(
                [
                    ("Hosts", str(len(group.hosts))),
                    ("Patterns", str(len(group.patterns))),
                ]
            ),
        )

    def _build_group_info(self, group: SSH_Group):
        """Render the wide description/info card for a selected group."""

        source_lines = self._get_group_source_lines(group)
        return RichGroup(
            self._detail_grid([("Description", group.desc or "...empty...")]),
            self._inner_rule(),
            self._detail_grid([("Info", "\n".join(group.info) if group.info else "...empty...")]),
            self._inner_rule(),
            self._detail_grid([("Source", "\n".join(source_lines) if source_lines else "Current config")]),
        )

    def _build_group_hosts(self, group: SSH_Group):
        """Render the host list that belongs to a selected group."""

        hosts_table = self._compact_table()
        hosts_table.add_column("Host", width=20, max_width=20, no_wrap=True, overflow="ellipsis")
        hosts_table.add_column("Type", width=7, max_width=7, no_wrap=True)
        hosts_table.add_column("Address:Port", width=21, max_width=21, no_wrap=True, overflow="ellipsis")
        hosts_table.add_column("Source", ratio=1, no_wrap=True, overflow="ellipsis")

        for host in group.hosts + group.patterns:
            # Resolve displayed endpoint from the effective SSH parameters, not
            # only from the host-local block, so inherited values show correctly.
            address, _ = host.get_applied_param("hostname")
            port, _ = host.get_applied_param("port")
            endpoint = self._format_endpoint(address, port)
            hosts_table.add_row(host.name, host.type.value, endpoint, host.get_source_label() or "Current config")

        if hosts_table.row_count == 0:
            return "This group does not contain any hosts or patterns."
        return hosts_table

    def _build_host_identity(self, host: SSH_Host):
        """Render the basic identity card for a selected host."""

        return RichGroup(
            self._detail_grid([("Name", host.name)]),
            self._inner_rule(),
            self._detail_grid(
                [
                    ("Group", host.group),
                    ("Type", host.type.value),
                ]
            ),
            self._inner_rule(),
            self._detail_grid(
                [
                    ("Alt names", ", ".join(host.alt_names) if host.alt_names else "..."),
                    ("Source", host.get_source_label() or "Current config"),
                ]
            ),
        )

    def _build_host_connection(self, host: SSH_Host):
        """Render the connection-focused card for a selected host."""

        hostname, _ = host.get_applied_param("hostname")
        port, _ = host.get_applied_param("port")
        user, _ = host.get_applied_param("user")
        identity_file, _ = host.get_applied_param("identityfile")

        endpoint = self._format_endpoint(hostname, port)
        return RichGroup(
            self._detail_grid(
                [
                    ("Endpoint", endpoint),
                    ("User", user or "..."),
                ]
            ),
            self._inner_rule(),
            self._detail_grid([("Identity", self._format_param_value(identity_file) if identity_file else "...")]),
        )

    def _build_host_info(self, host: SSH_Host):
        """Render the free-form SSHClick metadata lines for a host."""

        return "\n".join(host.info) if host.info else "...empty..."

    def _build_host_params(self, host: SSH_Host):
        """Render effective SSH parameters together with inheritance sources."""

        params_table = self._compact_table()
        params_table.add_column("Param", width=20, max_width=20, no_wrap=True, overflow="ellipsis")
        params_table.add_column("Value", width=20, max_width=20, no_wrap=True, overflow="ellipsis")
        params_table.add_column("Inherited from", ratio=1)

        for param in sorted(host.get_all_params()):
            value, source = host.get_applied_param(param)
            output_value = self._format_param_value(value)
            inherited = "" if source == "local" else source
            row_style = self._param_row_style(source)
            params_table.add_row(param, output_value, inherited, style=row_style)

        if params_table.row_count == 0:
            return "No SSH parameters found for this host."
        return params_table

    def _build_host_connectivity_route(self, host: SSH_Host):
        """Render the main route and jump information for the connectivity tab."""

        hostname, _ = host.get_applied_param("hostname")
        port, _ = host.get_applied_param("port")
        user, _ = host.get_applied_param("user")
        proxyjump, proxyjump_source = host.get_applied_param("proxyjump")

        route_via = self._format_param_value(proxyjump) if proxyjump else "direct"
        if route_via != "direct" and proxyjump_source not in {"", "local"}:
            route_via = f"{route_via} ({proxyjump_source})"

        return RichGroup(
            self._detail_grid(
                [
                    ("Endpoint", self._format_endpoint(hostname, port)),
                    ("User", user or "..."),
                ]
            ),
            self._inner_rule(),
            self._detail_grid([("Via", route_via)]),
        )

    def _build_host_connectivity_tunnels(self, host: SSH_Host):
        """Render SSH tunnel configuration in a compact connectivity card."""

        return RichGroup(
            self._detail_grid(
                [
                    ("Local", self._format_connectivity_value(host.get_applied_param("localforward")[0])),
                    ("Remote", self._format_connectivity_value(host.get_applied_param("remoteforward")[0])),
                    ("Dynamic", self._format_connectivity_value(host.get_applied_param("dynamicforward")[0])),
                ]
            )
        )

    def _build_host_connectivity_graph(self, host: SSH_Host):
        """Render the shared SSH connection graph for a selected host."""

        traced_hosts = self.sshconf.trace_proxyjump(host.name)
        if traced_hosts is None:
            return "Unable to calculate the SSH proxy chain for this host."
        graph = generate_graph(traced_hosts, print_tunnels=True, show_title=False)
        return graph

    def _get_group_source_lines(self, group: SSH_Group) -> list[str]:
        """Return deduplicated source references that define the given group."""

        seen_sources = set()
        source_lines = []
        source_refs = group.source_refs if group.source_refs else [(host.source_file, host.source_line) for host in group.hosts + group.patterns if host.source_file]

        for source_file, source_line in source_refs:
            if not source_file:
                continue
            source_ref = f"{source_file}:{source_line}"
            if source_ref in seen_sources:
                continue
            seen_sources.add(source_ref)
            source_lines.append(source_ref)

        return source_lines

    def _theme_var(self, name: str, fallback: str) -> str:
        return getattr(self.app, "theme_variables", {}).get(name, fallback) if self.is_mounted else fallback

    def _switcher(self) -> ContentSwitcher:
        """Return the main content switcher used for empty, group, and host views."""

        return self.query_one("#details_switcher", ContentSwitcher)

    def _show_empty_state(self) -> None:
        """Display the empty inspector placeholder."""

        self._switcher().display = False
        self.call_after_refresh(self._sync_scrollbar_visibility)

    def _show_group(self, group: SSH_Group) -> None:
        """Display the group-specific inspector view."""

        self._switcher().display = True
        self._switcher().current = "details_group_view"
        self.query_one("#group_summary_card", Static).update(self._build_group_overview(group))
        self.query_one("#group_info_card", Static).update(self._build_group_info(group))
        self.query_one("#group_hosts_card", Static).update(self._build_group_hosts(group))
        self.call_after_refresh(self._sync_scrollbar_visibility)

    def _show_host(self, host: SSH_Host) -> None:
        """Display the host-specific inspector view and both host tabs."""

        self._switcher().display = True
        self._switcher().current = "details_host_view"
        self.query_one("#host_identity_card", Static).update(self._build_host_identity(host))
        self.query_one("#host_connection_card", Static).update(self._build_host_connection(host))
        self.query_one("#host_info_card", Static).update(self._build_host_info(host))
        self.query_one("#host_params_card", Static).update(self._build_host_params(host))
        self.query_one("#host_connectivity_route_card", Static).update(self._build_host_connectivity_route(host))
        self.query_one("#host_connectivity_tunnels_card", Static).update(self._build_host_connectivity_tunnels(host))
        self.query_one("#host_connectivity_graph_card", Static).update(self._build_host_connectivity_graph(host))
        self.call_after_refresh(self._sync_scrollbar_visibility)

    def _detail_grid(self, rows: list[tuple[str, str]]) -> Table:
        """Create a compact two-column key/value grid for bordered cards."""

        table = Table.grid(expand=True)
        table.add_column(style=self._theme_var("accent", "cyan"), no_wrap=True, width=12)
        table.add_column(ratio=1)
        for key, value in rows:
            table.add_row(key, value)
        return table

    def _compact_table(self) -> Table:
        """Create a compact inner table that relies on the outer card border."""

        return Table(
            box=MINIMAL,
            show_edge=False,
            pad_edge=False,
            collapse_padding=True,
            expand=True,
            style=self._theme_var("sshclick-muted", "grey50"),
            border_style=self._border_color(),
        )

    def _format_endpoint(self, address: str, port: str) -> str:
        """Render a host endpoint in the form address:port when both exist."""

        endpoint = address if address else "..."
        if endpoint != "..." and port:
            endpoint = f"{endpoint}:{port}"
        return endpoint

    def _format_param_value(self, value) -> str:
        """Flatten SSH parameter values into readable table cell content."""

        return value if not isinstance(value, list) else "\n".join(value)

    def _format_connectivity_value(self, value) -> str:
        """Flatten connectivity values while keeping empty tunnel state readable."""

        formatted = self._format_param_value(value)
        return formatted if formatted else "none"

    def _param_row_style(self, source: str) -> str:
        """Return the row color used to distinguish local, global, and matched values."""

        if source == "global":
            return self._theme_var("success", "green")
        if source not in {"", "local"}:
            return self._theme_var("warning", "yellow")
        return ""

    def _add_network_rows(self, table: Table, host: SSH_Host, *keys: str) -> None:
        """Append network summary rows for the given effective SSH parameters."""

        for key in keys:
            value, source = host.get_applied_param(key)
            if not value:
                continue
            source_suffix = "" if source in {"", "local"} else f" ({source})"
            table.add_row(key, f"{self._format_param_value(value)}{source_suffix}")

    def _border_color(self) -> str:
        return self._theme_var("sshclick-border", "grey35")

    def _inner_rule(self) -> Rule:
        """Create a subtle divider used to split sections inside a bordered card."""

        return Rule(style=self._border_color(), characters="─")

    def _set_card_titles(self) -> None:
        """Assign stable border titles to the inspector cards."""

        card_titles = {
            "group_summary_card": "Group",
            "group_info_card": "Details",
            "group_hosts_card": "Members",
            "host_identity_card": "Host",
            "host_connection_card": "Connection",
            "host_info_card": "Info",
            "host_params_card": "SSH parameters",
            "host_connectivity_route_card": "Route",
            "host_connectivity_tunnels_card": "Tunnels",
            "host_connectivity_graph_card": "Connection graph",
        }

        for widget_id, title in card_titles.items():
            self.query_one(f"#{widget_id}", Static).border_title = title

    def _sync_scrollbar_visibility(self) -> None:
        """Hide tiny phantom scrollbars when the content effectively fits."""
        # Textual doesn't have an automatic "show only when needed" scrollbar
        # mode here, so we hide tiny phantom scrollbars ourselves.
        self.styles.scrollbar_visibility = "visible" if self.max_scroll_y > 1 else "hidden"
