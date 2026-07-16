from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QDateEdit,
    QComboBox,
    QHeaderView,
    QAbstractItemView,
)

from motocontrol.database.repositories import VehicleRepository
from motocontrol.services.validation import validate_placa
from motocontrol.ui.helpers import (
    create_search_field,
    filter_table_rows,
    format_currency,
    format_date,
    notify_data_changed,
    setup_data_table,
    set_table_item,
)


class VehicleFormDialog(QDialog):
    def __init__(self, vehicle: dict | None = None, parent=None):
        super().__init__(parent)
        self.vehicle = vehicle
        self.setWindowTitle("Editar Veículo" if vehicle else "Novo Veículo")
        self.setMinimumWidth(420)
        layout = QFormLayout(self)
        self.marca = QLineEdit(vehicle["marca"] if vehicle else "")
        self.modelo = QLineEdit(vehicle["modelo"] if vehicle else "")
        self.ano = QSpinBox()
        self.ano.setRange(1980, 2100)
        self.ano.setValue(vehicle["ano"] if vehicle else 2024)
        self.placa = QLineEdit(vehicle["placa"] if vehicle else "")
        self.renavam = QLineEdit(vehicle.get("renavam", "") if vehicle else "")
        self.data_compra = QDateEdit()
        self.data_compra.setCalendarPopup(True)
        self.data_compra.setDisplayFormat("dd/MM/yyyy")
        if vehicle and vehicle.get("data_compra"):
            d = QDate.fromString(vehicle["data_compra"], "yyyy-MM-dd")
            if d.isValid():
                self.data_compra.setDate(d)
        self.valor_compra = QDoubleSpinBox()
        self.valor_compra.setRange(0, 9999999)
        self.valor_compra.setPrefix("R$ ")
        self.valor_compra.setValue(vehicle.get("valor_compra", 0) if vehicle else 0)
        self.capacidade_tanque = QDoubleSpinBox()
        self.capacidade_tanque.setRange(0, 200)
        self.capacidade_tanque.setDecimals(1)
        self.capacidade_tanque.setSuffix(" L")
        self.capacidade_tanque.setValue(vehicle.get("capacidade_tanque", 0) if vehicle else 0)
        layout.addRow("Marca:", self.marca)
        layout.addRow("Modelo:", self.modelo)
        layout.addRow("Ano:", self.ano)
        layout.addRow("Placa:", self.placa)
        layout.addRow("Renavam:", self.renavam)
        layout.addRow("Data da Compra:", self.data_compra)
        layout.addRow("Valor da Compra:", self.valor_compra)
        layout.addRow("Capacidade do Tanque:", self.capacidade_tanque)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> dict:
        return {
            "marca": self.marca.text().strip(),
            "modelo": self.modelo.text().strip(),
            "ano": self.ano.value(),
            "placa": self.placa.text().strip(),
            "renavam": self.renavam.text().strip(),
            "data_compra": self.data_compra.date().toString("yyyy-MM-dd"),
            "valor_compra": self.valor_compra.value(),
            "capacidade_tanque": self.capacidade_tanque.value(),
        }


class VehiclesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Cadastro de Veículos")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        btn_new = QPushButton("+ Novo Veículo")
        btn_new.clicked.connect(self._add)
        header.addWidget(btn_new)
        layout.addLayout(header)

        self.search = create_search_field("Buscar veículos...")
        self.search.textChanged.connect(lambda text: filter_table_rows(self.table, text))
        layout.addWidget(self.search)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Marca", "Modelo", "Ano", "Placa", "Renavam", "Compra", "Valor"]
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
        vehicles = VehicleRepository.list_all()
        self.table.setRowCount(len(vehicles))
        for row, v in enumerate(vehicles):
            set_table_item(self.table, row, 0, str(v["id"]), sort_value=v["id"])
            set_table_item(self.table, row, 1, v["marca"])
            set_table_item(self.table, row, 2, v["modelo"])
            set_table_item(self.table, row, 3, str(v["ano"]), sort_value=v["ano"])
            set_table_item(self.table, row, 4, v["placa"])
            set_table_item(self.table, row, 5, v.get("renavam", ""))
            set_table_item(
                self.table, row, 6, format_date(v.get("data_compra", "")),
                sort_value=v.get("data_compra", ""),
            )
            set_table_item(
                self.table, row, 7, format_currency(v.get("valor_compra", 0)),
                sort_value=v.get("valor_compra", 0),
            )
        filter_table_rows(self.table, self.search.text())

    def _save_vehicle(self, data: dict, vehicle_id: int | None = None) -> bool:
        if not data["marca"] or not data["placa"] or not data["modelo"]:
            QMessageBox.warning(self, "Validação", "Marca, modelo e placa são obrigatórios.")
            return False
        ok, result = validate_placa(data["placa"])
        if not ok:
            QMessageBox.warning(self, "Validação", result)
            return False
        data["placa"] = result
        try:
            if vehicle_id:
                VehicleRepository.update(vehicle_id, data)
            else:
                VehicleRepository.create(data)
        except Exception as exc:
            if "UNIQUE" in str(exc).upper():
                QMessageBox.warning(self, "Validação", "Esta placa já está cadastrada.")
            else:
                QMessageBox.critical(self, "Erro", str(exc))
            return False
        return True

    def _selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def _on_row_double_clicked(self, row: int, _col: int) -> None:
        self.table.selectRow(row)
        self._edit()

    def _add(self) -> None:
        dlg = VehicleFormDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            if self._save_vehicle(dlg.get_data()):
                notify_data_changed(self)

    def _edit(self) -> None:
        vid = self._selected_id()
        if not vid:
            QMessageBox.information(self, "Seleção", "Selecione um veículo.")
            return
        vehicle = VehicleRepository.get(vid)
        dlg = VehicleFormDialog(vehicle, self)
        if dlg.exec() == QDialog.Accepted:
            if self._save_vehicle(dlg.get_data(), vid):
                notify_data_changed(self)

    def _delete(self) -> None:
        vid = self._selected_id()
        if not vid:
            QMessageBox.information(self, "Seleção", "Selecione um veículo para excluir.")
            return
        vehicle = VehicleRepository.get(vid)
        label = f"{vehicle['placa']} ({vehicle['marca']} {vehicle['modelo']})" if vehicle else "selecionado"
        if QMessageBox.question(
            self,
            "Confirmar",
            f"Excluir {label}?\nTodos os abastecimentos, manutenções e documentos vinculados serão removidos.",
        ) == QMessageBox.Yes:
            VehicleRepository.delete(vid)
            notify_data_changed(self)
