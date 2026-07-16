from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QAbstractItemView,
    QLineEdit,
)

from motocontrol.config import FUEL_TYPES
from motocontrol.database.repositories import FuelingRepository, MaintenanceRepository, VehicleRepository
from motocontrol.services.calculations import compute_fueling_consumption, get_latest_odometer
from motocontrol.ui.helpers import (
    create_search_field,
    filter_table_rows,
    format_currency,
    format_date,
    format_number,
    notify_data_changed,
    repopulate_table,
    setup_data_table,
    set_table_item,
)
from motocontrol.ui.widgets.cards import VehicleFilterBar


class FuelingFormDialog(QDialog):
    def __init__(self, record: dict | None = None, parent=None):
        super().__init__(parent)
        self.record = record
        self.setWindowTitle("Editar Abastecimento" if record else "Novo Abastecimento")
        self.setMinimumWidth(420)
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
        self.litros = QDoubleSpinBox()
        self.litros.setRange(0.1, 500)
        self.litros.setDecimals(2)
        self.litros.setValue(1.0)
        self.valor = QDoubleSpinBox()
        self.valor.setRange(0.01, 99999)
        self.valor.setDecimals(2)
        self.valor.setPrefix("R$ ")
        self.valor.setValue(0.01)
        self.posto = QLineEdit()
        self.tipo = QComboBox()
        self.tipo.addItems(FUEL_TYPES)
        self.tanque_cheio = QCheckBox("Tanque cheio")
        self.tanque_cheio.setChecked(True)
        if record:
            idx = self.vehicle.findData(record["vehicle_id"])
            if idx >= 0:
                self.vehicle.setCurrentIndex(idx)
            d = QDate.fromString(record["data"], "yyyy-MM-dd")
            if d.isValid():
                self.data.setDate(d)
            self.quilometragem.setValue(record["quilometragem"])
            self.litros.setValue(record["litros"])
            self.valor.setValue(record["valor"])
            self.posto.setText(record.get("posto", ""))
            tidx = self.tipo.findText(record.get("tipo_combustivel", ""))
            if tidx >= 0:
                self.tipo.setCurrentIndex(tidx)
            self.tanque_cheio.setChecked(bool(record.get("tanque_cheio", 1)))
        self.vehicle.currentIndexChanged.connect(self._sync_odometer_hint)
        self._sync_odometer_hint()
        layout.addRow("Veículo:", self.vehicle)
        layout.addRow("Data:", self.data)
        layout.addRow("Quilometragem:", self.quilometragem)
        layout.addRow("Litros:", self.litros)
        layout.addRow("Valor:", self.valor)
        layout.addRow("Posto:", self.posto)
        layout.addRow("Combustível:", self.tipo)
        layout.addRow("", self.tanque_cheio)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._try_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _sync_odometer_hint(self) -> None:
        vehicle_id = self.vehicle.currentData()
        if not vehicle_id or self.record:
            return
        latest = get_latest_odometer(vehicle_id)
        if latest > 0 and self.quilometragem.value() <= 0:
            self.quilometragem.setValue(latest)

    def _try_accept(self) -> None:
        data = self.get_data()
        if not data["vehicle_id"]:
            QMessageBox.warning(self, "Validação", "Selecione um veículo.")
            return
        if data["litros"] <= 0:
            QMessageBox.warning(self, "Validação", "Informe a quantidade de litros.")
            return
        if data["valor"] <= 0:
            QMessageBox.warning(self, "Validação", "Informe o valor pago no abastecimento.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "vehicle_id": self.vehicle.currentData(),
            "data": self.data.date().toString("yyyy-MM-dd"),
            "quilometragem": self.quilometragem.value(),
            "litros": self.litros.value(),
            "valor": self.valor.value(),
            "posto": self.posto.text().strip(),
            "tipo_combustivel": self.tipo.currentText(),
            "tanque_cheio": self.tanque_cheio.isChecked(),
        }


def _validate_fueling_data(parent, data: dict, record_id: int | None = None) -> bool:
    if not data["vehicle_id"]:
        QMessageBox.warning(parent, "Validação", "Selecione um veículo.")
        return False
    if data["litros"] <= 0 or data["valor"] <= 0:
        QMessageBox.warning(parent, "Validação", "Litros e valor devem ser maiores que zero.")
        return False
    latest = get_latest_odometer(data["vehicle_id"])
    if latest > 0 and data["quilometragem"] < latest:
        answer = QMessageBox.question(
            parent,
            "Quilometragem",
            f"A quilometragem informada ({data['quilometragem']:.0f} km) é menor que "
            f"a última registrada ({latest:.0f} km). Deseja continuar mesmo assim?",
        )
        if answer != QMessageBox.Yes:
            return False
    return True


class FuelingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Abastecimentos")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        btn_new = QPushButton("+ Novo Abastecimento")
        btn_new.clicked.connect(self._add)
        header.addWidget(btn_new)
        layout.addLayout(header)

        filters = QHBoxLayout()
        self.filter_bar = VehicleFilterBar()
        filters.addWidget(self.filter_bar, 1)
        layout.addLayout(filters)

        self.summary = QLabel("")
        self.summary.setObjectName("subtitle")
        layout.addWidget(self.summary)

        self.search = create_search_field("Buscar abastecimentos...")
        self.search.textChanged.connect(lambda text: filter_table_rows(self.table, text))
        layout.addWidget(self.search)

        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Data", "Placa", "KM", "Litros", "Valor", "Posto", "Combustível", "Cheio", "KM/L", "R$/KM"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
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
        records = compute_fueling_consumption(
            FuelingRepository.list_all(vid),
            MaintenanceRepository.list_all(vid),
        )
        records.sort(key=lambda r: (r["data"], r["quilometragem"], r["id"]), reverse=True)

        km_l_values = [r["km_l"] for r in records if r["km_l"]]
        media = sum(km_l_values) / len(km_l_values) if km_l_values else 0
        self.summary.setText(
            f"Média de consumo (tanque cheio): {media:.2f} KM/L" if km_l_values else ""
        )

        def populate() -> None:
            self.table.setRowCount(len(records))
            for row, r in enumerate(records):
                set_table_item(self.table, row, 0, str(r["id"]), sort_value=r["id"])
                set_table_item(self.table, row, 1, format_date(r["data"]), sort_value=r["data"])
                set_table_item(self.table, row, 2, r["placa"])
                set_table_item(
                    self.table, row, 3, format_number(r["quilometragem"], decimals=0),
                    sort_value=r["quilometragem"],
                )
                set_table_item(self.table, row, 4, format_number(r["litros"]), sort_value=r["litros"])
                set_table_item(self.table, row, 5, format_currency(r["valor"]), sort_value=r["valor"])
                set_table_item(self.table, row, 6, r.get("posto", ""))
                set_table_item(self.table, row, 7, r.get("tipo_combustivel", ""))
                set_table_item(self.table, row, 8, "Sim" if r.get("tanque_cheio", 1) else "Não")
                set_table_item(
                    self.table, row, 9,
                    format_number(r["km_l"]) if r["km_l"] else "-",
                    sort_value=r["km_l"] or 0,
                )
                set_table_item(
                    self.table, row, 10,
                    format_currency(r["custo_km"]) if r["custo_km"] else "-",
                    sort_value=r["custo_km"] or 0,
                )

        repopulate_table(self.table, populate, sort_column=1, sort_descending=True)
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
        dlg = FuelingFormDialog(parent=self)
        preselected = self.filter_bar.selected_vehicle_id()
        if preselected:
            idx = dlg.vehicle.findData(preselected)
            if idx >= 0:
                dlg.vehicle.setCurrentIndex(idx)
        if dlg.exec() != QDialog.Accepted:
            return
        data = dlg.get_data()
        if not _validate_fueling_data(self, data):
            return
        FuelingRepository.create(data)
        selected = self.filter_bar.selected_vehicle_id()
        if selected is not None and selected != data["vehicle_id"]:
            self.filter_bar.set_vehicle_id(data["vehicle_id"])
        notify_data_changed(self)

    def _edit(self) -> None:
        fid = self._selected_id()
        if not fid:
            QMessageBox.information(self, "Seleção", "Selecione um abastecimento para editar.")
            return
        records = {r["id"]: r for r in FuelingRepository.list_all()}
        dlg = FuelingFormDialog(records[fid], self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if not _validate_fueling_data(self, data, fid):
                return
            FuelingRepository.update(fid, data)
            notify_data_changed(self)

    def _delete(self) -> None:
        fid = self._selected_id()
        if not fid:
            QMessageBox.information(self, "Seleção", "Selecione um abastecimento para excluir.")
            return
        if QMessageBox.question(self, "Confirmar", "Excluir abastecimento?") == QMessageBox.Yes:
            FuelingRepository.delete(fid)
            notify_data_changed(self)
