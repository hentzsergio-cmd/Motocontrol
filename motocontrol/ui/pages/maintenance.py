from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
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
    QTextEdit,
)

from motocontrol.config import MAINTENANCE_CATEGORIES
from motocontrol.database.repositories import MaintenanceRepository, VehicleRepository
from motocontrol.services.calculations import get_latest_odometer
from motocontrol.ui.helpers import (
    create_search_field,
    filter_table_rows,
    format_currency,
    format_date,
    format_number,
    notify_data_changed,
    setup_data_table,
    set_table_item,
)
from motocontrol.ui.widgets.cards import VehicleFilterBar


class MaintenanceFormDialog(QDialog):
    def __init__(self, record: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Manutenção" if record else "Nova Manutenção")
        self.setMinimumWidth(460)
        layout = QFormLayout(self)
        self.vehicle = QComboBox()
        for v in VehicleRepository.list_all():
            self.vehicle.addItem(f"{v['placa']} — {v['marca']} {v['modelo']}", v["id"])
        self.data = QDateEdit()
        self.data.setCalendarPopup(True)
        self.data.setDisplayFormat("dd/MM/yyyy")
        self.data.setDate(QDate.currentDate())
        self.quilometragem = QDoubleSpinBox()
        self.quilometragem.setRange(0, 9999999)
        self.quilometragem.setDecimals(1)
        self.km_hint = QLabel()
        self.km_hint.setWordWrap(True)
        self.km_hint.setStyleSheet("color: #888; font-size: 11px;")
        self.categoria = QComboBox()
        self.categoria.addItems(MAINTENANCE_CATEGORIES)
        self.descricao = QTextEdit()
        self.descricao.setMaximumHeight(80)
        self.oficina = QLineEdit()
        self.valor = QDoubleSpinBox()
        self.valor.setRange(0, 999999)
        self.valor.setPrefix("R$ ")
        if record:
            idx = self.vehicle.findData(record["vehicle_id"])
            if idx >= 0:
                self.vehicle.setCurrentIndex(idx)
            d = QDate.fromString(record["data"], "yyyy-MM-dd")
            if d.isValid():
                self.data.setDate(d)
            self.quilometragem.setValue(record["quilometragem"])
            cidx = self.categoria.findText(record["categoria"])
            if cidx >= 0:
                self.categoria.setCurrentIndex(cidx)
            self.descricao.setPlainText(record.get("descricao", ""))
            self.oficina.setText(record.get("oficina", ""))
            self.valor.setValue(record.get("valor", 0))
        layout.addRow("Veículo:", self.vehicle)
        layout.addRow("Data:", self.data)
        layout.addRow("Quilometragem:", self.quilometragem)
        layout.addRow("", self.km_hint)
        layout.addRow("Categoria:", self.categoria)
        self.categoria.currentTextChanged.connect(self._update_km_hint)
        self._update_km_hint(self.categoria.currentText())
        layout.addRow("Descrição:", self.descricao)
        layout.addRow("Oficina:", self.oficina)
        layout.addRow("Valor:", self.valor)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _update_km_hint(self, categoria: str) -> None:
        if categoria == "Revisão":
            self.km_hint.setText(
                "Marco da revisão no manual (ex.: 1.000 km). Não altera o KM Atual do dashboard."
            )
        else:
            self.km_hint.setText(
                "Quilometragem do hodômetro na data do serviço. O KM Atual vem dos abastecimentos."
            )

    def _on_accept(self) -> None:
        if self._validate():
            self.accept()

    def _validate(self) -> bool:
        vehicle_id = self.vehicle.currentData()
        km = self.quilometragem.value()
        if not vehicle_id or km <= 0:
            return True

        latest = get_latest_odometer(vehicle_id)
        if latest <= 0 or km <= latest * 1.5:
            return True

        categoria = self.categoria.currentText()
        if categoria == "Revisão":
            msg = (
                f"A quilometragem informada ({format_number(km, decimals=0)} km) é bem maior "
                f"que o hodômetro por abastecimentos ({format_number(latest, decimals=1)} km).\n\n"
                "Para revisões, informe o marco do manual (ex.: 1.000 km na 1ª revisão). "
                "Isso não altera o KM Atual do dashboard.\n\n"
                "Deseja continuar?"
            )
        else:
            msg = (
                f"A quilometragem ({format_number(km, decimals=0)} km) é bem maior que a "
                f"última leitura por abastecimento ({format_number(latest, decimals=1)} km).\n\n"
                "Manutenções não atualizam o KM Atual do dashboard.\n\n"
                "Deseja continuar?"
            )
        return QMessageBox.question(self, "Confirmar quilometragem", msg) == QMessageBox.Yes

    def get_data(self) -> dict:
        return {
            "vehicle_id": self.vehicle.currentData(),
            "data": self.data.date().toString("yyyy-MM-dd"),
            "quilometragem": self.quilometragem.value(),
            "categoria": self.categoria.currentText(),
            "descricao": self.descricao.toPlainText().strip(),
            "oficina": self.oficina.text().strip(),
            "valor": self.valor.value(),
        }


class MaintenancePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Manutenções")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        btn_new = QPushButton("+ Nova Manutenção")
        btn_new.clicked.connect(self._add)
        header.addWidget(btn_new)
        layout.addLayout(header)

        filters = QHBoxLayout()
        self.filter_bar = VehicleFilterBar()
        filters.addWidget(self.filter_bar, 1)
        layout.addLayout(filters)

        self.search = create_search_field("Buscar manutenções...")
        self.search.textChanged.connect(lambda text: filter_table_rows(self.table, text))
        layout.addWidget(self.search)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Data", "Placa", "KM", "Categoria", "Descrição", "Oficina", "Valor", "Veículo"]
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
        records = MaintenanceRepository.list_all(vid)
        self.table.setRowCount(len(records))
        for row, r in enumerate(records):
            set_table_item(self.table, row, 0, str(r["id"]), sort_value=r["id"])
            set_table_item(self.table, row, 1, format_date(r["data"]), sort_value=r["data"])
            set_table_item(self.table, row, 2, r["placa"])
            set_table_item(
                self.table, row, 3, format_number(r["quilometragem"], decimals=0),
                sort_value=r["quilometragem"],
            )
            set_table_item(self.table, row, 4, r["categoria"])
            set_table_item(self.table, row, 5, r.get("descricao", ""))
            set_table_item(self.table, row, 6, r.get("oficina", ""))
            set_table_item(
                self.table, row, 7, format_currency(r.get("valor", 0)),
                sort_value=r.get("valor", 0),
            )
            set_table_item(self.table, row, 8, f"{r['marca']} {r['modelo']}")
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
        if not VehicleRepository.list_all():
            QMessageBox.warning(self, "Aviso", "Cadastre um veículo primeiro.")
            return
        dlg = MaintenanceFormDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            MaintenanceRepository.create(dlg.get_data())
            notify_data_changed(self)

    def _edit(self) -> None:
        mid = self._selected_id()
        if not mid:
            QMessageBox.information(self, "Seleção", "Selecione uma manutenção para editar.")
            return
        records = {r["id"]: r for r in MaintenanceRepository.list_all()}
        dlg = MaintenanceFormDialog(records[mid], self)
        if dlg.exec() == QDialog.Accepted:
            MaintenanceRepository.update(mid, dlg.get_data())
            notify_data_changed(self)

    def _delete(self) -> None:
        mid = self._selected_id()
        if not mid:
            QMessageBox.information(self, "Seleção", "Selecione uma manutenção para excluir.")
            return
        if QMessageBox.question(self, "Confirmar", "Excluir manutenção?") == QMessageBox.Yes:
            MaintenanceRepository.delete(mid)
            notify_data_changed(self)
