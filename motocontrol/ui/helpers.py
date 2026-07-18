from datetime import datetime
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QLineEdit, QTableWidget, QTableWidgetItem, QWidget


class SortableTableWidgetItem(QTableWidgetItem):
    """Ordena por UserRole (ISO/número) quando disponível — datas dd/MM/yyyy ficam corretas."""

    def __lt__(self, other: QTableWidgetItem) -> bool:
        if not isinstance(other, QTableWidgetItem):
            return super().__lt__(other)
        left = self.data(Qt.ItemDataRole.UserRole)
        right = other.data(Qt.ItemDataRole.UserRole)
        if left is not None and right is not None:
            try:
                return left < right
            except TypeError:
                return str(left) < str(right)
        return super().__lt__(other)


def notify_data_changed(widget: QWidget) -> None:
    window = widget.window()
    if hasattr(window, "refresh_all"):
        window.refresh_all()
    elif hasattr(widget, "refresh"):
        widget.refresh()


def format_number(value: float | int | None, suffix: str = "", decimals: int = 2) -> str:
    if value is None:
        return "-"
    if isinstance(value, (int, float)):
        return (
            f"{value:,.{decimals}f}{suffix}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    return str(value)


def format_currency(value: float | int | None) -> str:
    formatted = format_number(value)
    return "-" if formatted == "-" else f"R$ {formatted}"


def format_km(value: float | int | None) -> str:
    return format_number(value, " km", decimals=0)


def format_consumption(value: float | int | None) -> str:
    return format_number(value, " km/L")


def format_autonomia(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{format_number(value, decimals=0)} km/tanque"


def format_custo_km(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"R$ {format_number(value, decimals=4)}/km"


def format_date(iso_date: str) -> str:
    if not iso_date:
        return "-"
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(iso_date[:10], fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return iso_date


def format_document_countdown(days: int) -> str:
    if days < 0:
        return f"Vencido há {abs(days)} dias"
    if days == 0:
        return "Vence hoje"
    return f"{days} dias"


def setup_data_table(table: QTableWidget, *, hide_id: bool = True) -> None:
    if hide_id:
        table.setColumnHidden(0, True)
    table.setSortingEnabled(True)
    table.setAlternatingRowColors(True)
    header = table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.ResizeToContents)
    header.setStretchLastSection(True)
    header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)


def set_table_item(
    table: QTableWidget,
    row: int,
    col: int,
    text: str,
    *,
    sort_value: float | int | str | None = None,
) -> None:
    item = SortableTableWidgetItem(text) if sort_value is not None else QTableWidgetItem(text)
    if sort_value is not None:
        item.setData(Qt.ItemDataRole.UserRole, sort_value)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    table.setItem(row, col, item)


def repopulate_table(
    table: QTableWidget,
    populate: Callable[[], None],
    *,
    sort_column: int = 1,
    sort_descending: bool = True,
) -> None:
    """Preenche tabela sem embaralhar linhas e aplica ordenação estável."""
    table.setSortingEnabled(False)
    populate()
    table.setSortingEnabled(True)
    order = Qt.SortOrder.DescendingOrder if sort_descending else Qt.SortOrder.AscendingOrder
    table.sortItems(sort_column, order)


def create_search_field(placeholder: str = "Buscar...") -> QLineEdit:
    field = QLineEdit()
    field.setPlaceholderText(placeholder)
    field.setClearButtonEnabled(True)
    return field


def filter_table_rows(table: QTableWidget, query: str) -> None:
    text = query.strip().lower()
    for row in range(table.rowCount()):
        if not text:
            table.setRowHidden(row, False)
            continue
        row_text = " ".join(
            table.item(row, col).text()
            for col in range(table.columnCount())
            if table.item(row, col)
        ).lower()
        table.setRowHidden(row, text not in row_text)
