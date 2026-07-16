from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QAbstractItemView,
)

from motocontrol.config import FINANCIAL_CATEGORIES
from motocontrol.database.repositories import FinancialRepository, VehicleRepository
from motocontrol.services.calculations import get_financial_summary, get_latest_odometer
from motocontrol.ui.helpers import (
    create_search_field,
    filter_table_rows,
    format_currency,
    format_custo_km,
    format_date,
    notify_data_changed,
    setup_data_table,
    set_table_item,
)
from motocontrol.ui.widgets.cards import StatCard, VehicleFilterBar


class FinancialFormDialog(QDialog):
    def __init__(self, record: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Lançamento" if record else "Novo Lançamento")
        self.setMinimumWidth(420)
        layout = QFormLayout(self)
        self.vehicle = QComboBox()
        self.vehicle.addItem("Geral (sem veículo)", None)
        for v in VehicleRepository.list_all():
            self.vehicle.addItem(f"{v['placa']} — {v['marca']} {v['modelo']}", v["id"])
        self.data = QDateEdit()
        self.data.setCalendarPopup(True)
        self.data.setDisplayFormat("dd/MM/yyyy")
        self.data.setDate(QDate.currentDate())
        self.categoria = QComboBox()
        self.categoria.addItems(FINANCIAL_CATEGORIES)
        self.descricao = QLineEdit()
        self.valor = QDoubleSpinBox()
        self.valor.setRange(0, 9999999)
        self.valor.setPrefix("R$ ")
        if record:
            idx = self.vehicle.findData(record.get("vehicle_id"))
            if idx >= 0:
                self.vehicle.setCurrentIndex(idx)
            d = QDate.fromString(record["data"], "yyyy-MM-dd")
            if d.isValid():
                self.data.setDate(d)
            cidx = self.categoria.findText(record["categoria"])
            if cidx >= 0:
                self.categoria.setCurrentIndex(cidx)
            self.descricao.setText(record.get("descricao", ""))
            self.valor.setValue(record["valor"])
        layout.addRow("Veículo:", self.vehicle)
        layout.addRow("Data:", self.data)
        layout.addRow("Categoria:", self.categoria)
        layout.addRow("Descrição:", self.descricao)
        layout.addRow("Valor:", self.valor)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> dict:
        return {
            "vehicle_id": self.vehicle.currentData(),
            "data": self.data.date().toString("yyyy-MM-dd"),
            "categoria": self.categoria.currentText(),
            "descricao": self.descricao.text().strip(),
            "valor": self.valor.value(),
        }


class FinancialPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Financeiro")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        btn_new = QPushButton("+ Novo Lançamento")
        btn_new.clicked.connect(self._add)
        header.addWidget(btn_new)
        layout.addLayout(header)

        hint = QLabel(
            "Use esta tela para despesas extras (Seguro, Acessórios, Lavagens). "
            "Combustível, manutenções e documentos já entram nos totais pelos módulos próprios."
        )
        hint.setObjectName("subtitle")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        filters = QHBoxLayout()
        self.filter_bar = VehicleFilterBar()
        filters.addWidget(self.filter_bar, 1)
        layout.addLayout(filters)

        stats = QGridLayout()
        self.card_mensal = StatCard("Gasto Mensal (R$)")
        self.card_anual = StatCard("Gasto Anual (R$)")
        self.card_custo = StatCard("Custo por KM (R$)")
        self.card_total = StatCard("Total Investido (R$)")
        stats.addWidget(self.card_mensal, 0, 0)
        stats.addWidget(self.card_anual, 0, 1)
        stats.addWidget(self.card_custo, 0, 2)
        stats.addWidget(self.card_total, 0, 3)
        layout.addLayout(stats)

        self.search = create_search_field("Buscar lançamentos...")
        self.search.textChanged.connect(lambda text: filter_table_rows(self.table, text))
        layout.addWidget(self.search)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Data", "Categoria", "Descrição", "Valor", "Placa", "Veículo"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        setup_data_table(self.table)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self.table)

        actions = QHBoxLayout()
        btn_edit = QPushButton("Editar")
        btn_edit.setObjectName("secondaryBtn")
        btn_edit.clicked.connect(self._edit)
        btn_del = QPushButton("Excluir")
        btn_del.setObjectName("dangerBtn")
        btn_del.clicked.connect(self._delete)
        actions.addStretch()
        actions.addWidget(btn_edit)
        actions.addWidget(btn_del)
        layout.addLayout(actions)

    def refresh(self) -> None:
        self.filter_bar.refresh()
        vid = self.filter_bar.selected_vehicle_id()
        summary = get_financial_summary(vid)
        self.card_mensal.set_value(format_currency(summary["gasto_mensal"]))
        self.card_anual.set_value(format_currency(summary["gasto_anual"]))
        custo = summary["custo_km"]
        self.card_custo.set_value(format_custo_km(custo))
        self.card_total.set_value(format_currency(summary["total_investido"]))

        records = FinancialRepository.list_all(vid)
        self.table.setRowCount(len(records))
        for row, r in enumerate(records):
            placa = r.get("placa") or "-"
            veiculo = f"{r.get('marca', '')} {r.get('modelo', '')}".strip() or "-"
            set_table_item(self.table, row, 0, str(r["id"]), sort_value=r["id"])
            set_table_item(self.table, row, 1, format_date(r["data"]), sort_value=r["data"])
            set_table_item(self.table, row, 2, r["categoria"])
            set_table_item(self.table, row, 3, r.get("descricao", ""))
            set_table_item(self.table, row, 4, format_currency(r["valor"]), sort_value=r["valor"])
            set_table_item(self.table, row, 5, placa)
            set_table_item(self.table, row, 6, veiculo)
        filter_table_rows(self.table, self.search.text())

    def _selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def _on_row_double_clicked(self, row: int, _col: int) -> None:
        self.table.selectRow(row)
        self._edit()

    def _add(self) -> None:
        dlg = FinancialFormDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if data["valor"] <= 0:
                QMessageBox.warning(self, "Validação", "Informe um valor maior que zero.")
                return
            FinancialRepository.create(data)
            notify_data_changed(self)

    def _edit(self) -> None:
        eid = self._selected_id()
        if not eid:
            QMessageBox.information(self, "Seleção", "Selecione um lançamento para editar.")
            return
        records = {r["id"]: r for r in FinancialRepository.list_all()}
        dlg = FinancialFormDialog(records[eid], self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if data["valor"] <= 0:
                QMessageBox.warning(self, "Validação", "Informe um valor maior que zero.")
                return
            FinancialRepository.update(eid, data)
            notify_data_changed(self)

    def _delete(self) -> None:
        eid = self._selected_id()
        if not eid:
            QMessageBox.information(self, "Seleção", "Selecione um lançamento para excluir.")
            return
        if QMessageBox.question(self, "Confirmar", "Excluir lançamento?") == QMessageBox.Yes:
            FinancialRepository.delete(eid)
            notify_data_changed(self)
