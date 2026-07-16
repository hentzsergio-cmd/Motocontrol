from matplotlib import rc_context
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout

PIE_COLORS = ["#1a73e8", "#34a853", "#ea4335", "#fbbc04", "#9334e6", "#12b5cb", "#ff6d01"]


class ChartWidget(QFrame):
    def __init__(self, title: str, chart_type: str = "bar", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.chart_type = chart_type
        self._title = title
        self._theme = "dark"
        self.setMinimumHeight(260)
        self.setMaximumHeight(320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("chartTitle")

        self.figure = Figure(figsize=(5.2, 2.4), dpi=100, layout="constrained")
        self.figure.patch.set_alpha(0)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.canvas.setMinimumHeight(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 8)
        layout.setSpacing(4)
        layout.addWidget(self.title_label)
        layout.addWidget(self.canvas)

        self._update_title_style()

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self._update_title_style()

    def _theme_colors(self) -> dict[str, str]:
        if self._theme == "dark":
            return {
                "text": "#ffffff",
                "tick": "#b0b3b8",
                "spine": "#3c4043",
                "bg": "#1e1e1e",
                "grid": "#3c4043",
                "empty": "#9aa0a6",
            }
        return {
            "text": "#202124",
            "tick": "#5f6368",
            "spine": "#dadce0",
            "bg": "#ffffff",
            "grid": "#dadce0",
            "empty": "#80868b",
        }

    def _update_title_style(self) -> None:
        colors = self._theme_colors()
        self.title_label.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {colors['text']}; "
            "background: transparent; border: none; padding: 0;"
        )

    def _rc_params(self, colors: dict[str, str]) -> dict[str, str | float]:
        return {
            "text.color": colors["text"],
            "axes.labelcolor": colors["text"],
            "axes.titlecolor": colors["text"],
            "xtick.color": colors["tick"],
            "ytick.color": colors["tick"],
            "axes.edgecolor": colors["spine"],
            "axes.facecolor": colors["bg"],
            "figure.facecolor": "none",
            "grid.color": colors["grid"],
        }

    def _apply_theme(self, ax, colors: dict[str, str]) -> None:
        ax.set_facecolor(colors["bg"])
        ax.xaxis.label.set_color(colors["text"])
        ax.yaxis.label.set_color(colors["text"])
        ax.tick_params(colors=colors["tick"], labelsize=8)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color(colors["tick"])
        for spine in ax.spines.values():
            spine.set_color(colors["spine"])
        legend = ax.get_legend()
        if legend:
            for text in legend.get_texts():
                text.set_color(colors["text"])
        for line in ax.get_xgridlines() + ax.get_ygridlines():
            line.set_color(colors["grid"])

    def update_chart(self, labels: list, values: list, color: str = "#1a73e8") -> None:
        colors = self._theme_colors()
        self._update_title_style()

        with rc_context(self._rc_params(colors)):
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            if not labels or not values:
                ax.text(
                    0.5,
                    0.5,
                    "Sem dados",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    color=colors["empty"],
                    fontsize=11,
                )
                ax.set_axis_off()
            elif self.chart_type == "line":
                ax.plot(
                    range(len(labels)), values, marker="o", color=color, linewidth=2, markersize=5
                )
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
                ax.grid(True, alpha=0.25, linestyle="--")
                ax.margins(x=0.08, y=0.12)
            elif self.chart_type == "pie":
                pie_labels = [str(label)[:18] for label in labels]
                pie_text_color = colors["text"] if self._theme == "dark" else "#ffffff"
                wedges, _texts, autotexts = ax.pie(
                    values,
                    autopct="%1.0f%%",
                    startangle=90,
                    colors=PIE_COLORS[: len(values)],
                    pctdistance=0.75,
                    textprops={"fontsize": 8, "color": pie_text_color},
                )
                for autotext in autotexts:
                    autotext.set_fontweight("bold")
                ax.legend(
                    wedges,
                    pie_labels,
                    loc="center left",
                    bbox_to_anchor=(1.02, 0.5),
                    fontsize=7,
                    frameon=False,
                    labelcolor=colors["text"],
                )
                ax.set_aspect("equal")
            else:
                bar_width = min(0.55, max(0.25, 4.0 / max(len(labels), 1)))
                x_pos = range(len(labels))
                ax.bar(x_pos, values, color=color, width=bar_width)
                ax.set_xticks(list(x_pos))
                ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
                ax.grid(True, axis="y", alpha=0.25, linestyle="--")
                ax.margins(x=0.12, y=0.15)
                if len(values) == 1:
                    ax.set_xlim(-0.8, 0.8)

            self._apply_theme(ax, colors)

        self.canvas.draw()
