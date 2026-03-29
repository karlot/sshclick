from textual.app import ComposeResult
from rich.box import ROUNDED
from rich.console import Group as RenderGroup
from rich.panel import Panel
from rich.table import Table

from textual.containers import Vertical
from textual.widgets import ContentSwitcher, Label, Static, TabbedContent, TabPane

from sshclick.core import SSH_Config, SSH_Group, SSH_Host, generate_graph
from sshclick.ssht.state import SSHNode


class DetailsPane(Vertical):
    """Right-hand inspector that renders group and host details."""

    def __init__(self, sshconf: SSH_Config, id: str | None = None) -> None:
        self.sshconf = sshconf
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        yield Label("Select node from the list", id="details_header")
        # We keep group, host and empty states mounted and switch between them
        # so tab state and widget structure stay stable while the selection changes.
        with ContentSwitcher(initial="details_empty", id="details_switcher"):
            with Vertical(id="details_empty"):
                yield Static(
                    Panel("Select a group or host from the tree to inspect its details.", border_style=self._border_color()),
                    id="details_empty_panel",
                )

            with Vertical(id="details_group_view", classes="details_view"):
                yield Label("Group details", classes="details_section_title")
                yield Static(id="group_overview", classes="details_section_body")
                yield Label("Hosts in this group", classes="details_section_title")
                yield Static(id="group_hosts", classes="details_section_body")

            with Vertical(id="details_host_view", classes="details_view"):
                with TabbedContent(initial="host_overview_tab", id="host_tabs"):
                    with TabPane("Overview", id="host_overview_tab"):
                        with Vertical(classes="details_tab_scroll"):
                            yield Label("Details", classes="details_section_title")
                            yield Static(id="host_overview", classes="details_section_body")
                            yield Label("Info", classes="details_section_title")
                            yield Static(id="host_info", classes="details_section_body")
                            yield Label("SSH Parameters", classes="details_section_title")
                            yield Static(id="host_params", classes="details_section_body")
                    with TabPane("Network", id="host_network_tab"):
                        with Vertical(classes="details_tab_scroll"):
                            yield Label("Connection graph", classes="details_section_title")
                            yield Static(id="host_network", classes="details_section_body")

    def on_mount(self) -> None:
        self.call_after_refresh(self._sync_scrollbar_visibility)

    def on_resize(self, _event) -> None:
        self.call_after_refresh(self._sync_scrollbar_visibility)

    def update_config(self, sshconf: SSH_Config) -> None:
        """Replace the backing config model after a reload."""

        self.sshconf = sshconf

    def update_node(self, node: SSHNode) -> None:
        """Refresh the inspector for the currently selected group or host."""

        self.query_one("#details_header", Label).update(self._build_header(node))

        if node is None:
            self._show_empty_state()
            return

        if isinstance(node, SSH_Group):
            self._show_group(node)
            return

        self._show_host(node)

    def _build_header(self, node: SSHNode) -> str:
        if node is None:
            return "Select node from the list"
        if isinstance(node, SSH_Group):
            return f"Group: {node.name}"
        return f"Host: {node.name}"

    def _build_group_overview(self, group: SSH_Group):
        """Render the summary block shown for a selected group."""

        source_lines = self._get_group_source_lines(group)
        overview = self._summary_table()
        overview.add_column("Key", style=self._theme_var("accent", "cyan"), no_wrap=True)
        overview.add_column("Value")
        overview.add_row("Name", group.name)
        overview.add_row("Description", group.desc or "...empty...")
        overview.add_row("Info", "\n".join(group.info) if group.info else "...empty...")
        overview.add_row("Hosts", str(len(group.hosts)))
        overview.add_row("Patterns", str(len(group.patterns)))
        overview.add_row("Defined in", "\n".join(source_lines) if source_lines else "Current config")
        return overview

    def _build_group_hosts(self, group: SSH_Group):
        """Render the host list that belongs to a selected group."""

        hosts_table = self._data_table()
        hosts_table.add_column("Host", ratio=2)
        hosts_table.add_column("Type", width=9)
        hosts_table.add_column("Address:Port", ratio=2)
        hosts_table.add_column("Source", ratio=2)

        for host in group.hosts + group.patterns:
            # Resolve displayed endpoint from the effective SSH parameters, not
            # only from the host-local block, so inherited values show correctly.
            address, _ = host.get_applied_param("hostname")
            port, _ = host.get_applied_param("port")
            endpoint = self._format_endpoint(address, port)
            hosts_table.add_row(host.name, host.type.value, endpoint, host.get_source_label() or "Current config")

        if hosts_table.row_count == 0:
            return self._border_panel("This group does not contain any hosts or patterns.")
        return hosts_table

    def _build_host_overview(self, host: SSH_Host):
        """Render the basic identity details for a selected host."""

        overview = self._summary_table()
        overview.add_column("Key", style=self._theme_var("accent", "cyan"), no_wrap=True)
        overview.add_column("Value")
        overview.add_row("Name", host.name)
        overview.add_row("Group", host.group)
        overview.add_row("Type", host.type.value)
        overview.add_row("Alt names", ", ".join(host.alt_names) if host.alt_names else "...")
        overview.add_row("Source", host.get_source_label() or "Current config")
        return overview

    def _build_host_info(self, host: SSH_Host):
        """Render the free-form SSHClick metadata lines for a host."""

        content = "\n".join(host.info) if host.info else "...empty..."
        return self._border_panel(content)

    def _build_host_params(self, host: SSH_Host):
        """Render effective SSH parameters together with inheritance sources."""

        params_table = self._data_table()
        params_table.add_column("Param", ratio=1)
        params_table.add_column("Value", ratio=2)
        params_table.add_column("Inherited from", ratio=1)

        for param in sorted(host.get_all_params()):
            value, source = host.get_applied_param(param)
            output_value = self._format_param_value(value)
            inherited = "" if source == "local" else source
            row_style = self._param_row_style(source)
            params_table.add_row(param, output_value, inherited, style=row_style)

        if params_table.row_count == 0:
            return self._border_panel("No SSH parameters found for this host.")
        return params_table

    def _build_host_network(self, host: SSH_Host):
        """Render the network-focused host tab using the shared core graph logic."""

        traced_hosts = self.sshconf.trace_proxyjump(host.name)
        if traced_hosts is None:
            return Panel("Unable to calculate the SSH proxy chain for this host.", border_style=self._theme_var("error", "red"))

        summary = self._summary_table()
        summary.add_column("Detail", style=self._theme_var("accent", "cyan"), no_wrap=True)
        summary.add_column("Value")

        self._add_network_rows(summary, host, "hostname", "user", "port", "proxyjump")
        self._add_network_rows(summary, host, "localforward", "remoteforward", "dynamicforward")

        graph = generate_graph(traced_hosts, print_tunnels=True)
        return RenderGroup(
            Panel(
                summary if summary.row_count > 0 else "No explicit network parameters found.",
                title="Network summary",
                border_style=self._theme_var("sshclick-border", "grey35"),
            ),
            Panel(graph, title="SSH connection graph", border_style=self._theme_var("sshclick-border", "grey35")),
        )

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

        self._switcher().current = "details_empty"
        self.query_one("#details_empty_panel", Static).update(self._border_panel("Select a group or host from the tree to inspect its details."))
        self.call_after_refresh(self._sync_scrollbar_visibility)

    def _show_group(self, group: SSH_Group) -> None:
        """Display the group-specific inspector view."""

        self._switcher().current = "details_group_view"
        self.query_one("#group_overview", Static).update(self._build_group_overview(group))
        self.query_one("#group_hosts", Static).update(self._build_group_hosts(group))
        self.call_after_refresh(self._sync_scrollbar_visibility)

    def _show_host(self, host: SSH_Host) -> None:
        """Display the host-specific inspector view and both host tabs."""

        self._switcher().current = "details_host_view"
        self.query_one("#host_overview", Static).update(self._build_host_overview(host))
        self.query_one("#host_info", Static).update(self._build_host_info(host))
        self.query_one("#host_params", Static).update(self._build_host_params(host))
        self.query_one("#host_network", Static).update(self._build_host_network(host))
        self.call_after_refresh(self._sync_scrollbar_visibility)

    def _summary_table(self) -> Table:
        """Create a bordered two-column summary table with shared theme styling."""

        return Table(
            box=ROUNDED,
            show_header=False,
            expand=True,
            style=self._theme_var("sshclick-muted", "grey50"),
            border_style=self._border_color(),
        )

    def _data_table(self) -> Table:
        """Create a generic bordered data table using the shared border color."""

        return Table(box=ROUNDED, expand=True, border_style=self._border_color())

    def _border_panel(self, renderable) -> Panel:
        """Create a standard panel with the shared normal border color."""

        return Panel(renderable, border_style=self._border_color())

    def _format_endpoint(self, address: str, port: str) -> str:
        """Render a host endpoint in the form address:port when both exist."""

        endpoint = address if address else "..."
        if endpoint != "..." and port:
            endpoint = f"{endpoint}:{port}"
        return endpoint

    def _format_param_value(self, value) -> str:
        """Flatten SSH parameter values into readable table cell content."""

        return value if not isinstance(value, list) else "\n".join(value)

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

    def _sync_scrollbar_visibility(self) -> None:
        """Hide tiny phantom scrollbars when the content effectively fits."""
        # Textual doesn't have an automatic "show only when needed" scrollbar
        # mode here, so we hide tiny phantom scrollbars ourselves.
        self.styles.scrollbar_visibility = "visible" if self.max_scroll_y > 1 else "hidden"
