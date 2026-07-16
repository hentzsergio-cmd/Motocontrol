from datetime import datetime

from PySide6.QtCore import QDate
from PySide6.QtGui import QColor
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

from motocontrol.config import DOCUMENT_ALERT_DAYS, DOCUMENT_TYPES
from motocontrol.database.repositories import DocumentRepository, VehicleRepository
from motocontrol.services.calculations import get_document_alerts
from motocontrol.ui.helpers import (
    create_search_field,
    filter_table_rows,
    format_currency,
    format_date,
    format_document_countdown,
    notify_data_changed,
    setup_data_table,
    set_table_item,
)
from motocontrol.ui.widgets.cards import VehicleFilterBar


class DocumentFormDialog(QDialog):
    def __init__(self, record: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Documento" if record else "Novo Documento")
        self.setMinimumWidth(420)
        layout = QFormLayout(self)
        self.vehicle = QComboBox()
        for v in VehicleRepository.list_all():
            self.vehicle.addItem(f"{v['placa']} — {v['marca']} {v['modelo']}", v["id"])
        self.tipo = QComboBox()
        self.tipo.addItems(DOCUMENT_TYPES)
        self.descricao = QLineEdit()
        self.vencimento = QDateEdit()
        self.vencimento.setCalendarPopup(True)
        self.vencimento.setDisplayFormat("dd/MM/yyyy")
        self.valor = QDoubleSpinBox()
        self.valor.setRange(0, 999999)
        self.valor.setPrefix("R$ ")
        self.observacao = QTextEdit()
        self.observacao.setMaximumHeight(60)
        if record:
            idx = self.vehicle.findData(record["vehicle_id"])
            if idx >= 0:
                self.vehicle.setCurrentIndex(idx)
            tidx = self.tipo.findText(record["tipo"])
            if tidx >= 0:
                self.tipo.setCurrentIndex(tidx)
            self.descricao.setText(record.get("descricao", ""))
            d = QDate.fromString(record["data_vencimento"], "yyyy-MM-dd")
            if d.isValid():
                self.vencimento.setDate(d)
            self.valor.setValue(record.get("valor", 0))
            self.observacao.setPlainText(record.get("observacao", ""))
        layout.addRow("Veículo:", self.vehicle)
        layout.addRow("Tipo:", self.tipo)
        layout.addRow("Descrição:", self.descricao)
        layout.addRow("Vencimento:", self.vencimento)
        layout.addRow("Valor:", self.valor)
        layout.addRow("Observação:", self.observacao)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> dict:
        return {
            "vehicle_id": self.vehicle.currentData(),
            "tipo": self.tipo.currentText(),
            "descricao": self.descricao.text().strip(),
            "data_vencimento": self.vencimento.date().toString("yyyy-MM-dd"),
            "valor": self.valor.value(),
            "observacao": self.observacao.toPlainText().strip(),
        }


class DocumentsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Documentação")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        btn_new = QPushButton("+ Novo Documento")
        btn_new.clicked.connect(self._add)
        header.addWidget(btn_new)
        layout.addLayout(header)

        self.alert_label = QLabel("")
        self.alert_label.setObjectName("alert")
        self.alert_label.setWordWrap(True)
        layout.addWidget(self.alert_label)

        info = QLabel(f"Alertas automáticos: {', '.join(str(d) for d in DOCUMENT_ALERT_DAYS)} dias antes do vencimento")
        info.setObjectName("subtitle")
        layout.addWidget(info)

        filters = QHBoxLayout()
        self.filter_bar = VehicleFilterBar()
        filters.addWidget(self.filter_bar, 1)
        layout.addLayout(filters)

        self.search = create_search_field("Buscar documentos...")
        self.search.textChanged.connect(lambda text: filter_table_rows(self.table, text))
        layout.addWidget(self.search)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Tipo", "Placa", "Descrição", "Vencimento", "Dias", "Valor", "Observação"]
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
        records = DocumentRepository.list_all(vid)
        today = datetime.now().date()
        self.table.setRowCount(len(records))
        for row, r in enumerate(records):
            try:
                dt = datetime.strptime(r["data_vencimento"], "%Y-%m-%d").date()
                dias = (dt - today).days
            except ValueError:
                dias = "-"
            set_table_item(self.table, row, 0, str(r["id"]), sort_value=r["id"])
            set_table_item(self.table, row, 1, r["tipo"])
            set_table_item(self.table, row, 2, r["placa"])
            set_table_item(self.table, row, 3, r.get("descricao", ""))
            set_table_item(
                self.table, row, 4, format_date(r["data_vencimento"]),
                sort_value=r["data_vencimento"],
            )
            countdown = format_document_countdown(dias) if isinstance(dias, int) else str(dias)
            set_table_item(
                self.table, row, 5, countdown,
                sort_value=dias if isinstance(dias, int) else 9999,
            )
            set_table_item(
                self.table, row, 6, format_currency(r.get("valor", 0)),
                sort_value=r.get("valor", 0),
            )
            set_table_item(self.table, row, 7, r.get("observacao", ""))

            if isinstance(dias, int):
                color = None
                if dias < 0:
                    color = QColor("#d93025")
                elif dias <= 15:
                    color = QColor("#ea8600")
                elif dias <= 30:
                    color = QColor("#fbbc04")
                if color:
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item:
                            item.setForeground(color)

        alerts = get_document_alerts(vid)
        if alerts:
            lines = [
                f"⚠ {a['tipo']} — {a['placa']}: {format_document_countdown(a['dias_restantes'])}"
                for a in alerts
            ]
            self.alert_label.setText("\n".join(lines))
        else:
            self.alert_label.setText("Nenhum alerta de vencimento no momento.")
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
        dlg = DocumentFormDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            DocumentRepository.create(dlg.get_data())
            notify_data_changed(self)

    def _edit(self) -> None:
        did = self._selected_id()
        if not did:
            QMessageBox.information(self, "Seleção", "Selecione um documento para editar.")
            return
        records = {r["id"]: r for r in DocumentRepository.list_all()}
        dlg = DocumentFormDialog(records[did], self)
        if dlg.exec() == QDialog.Accepted:
            DocumentRepository.update(did, dlg.get_data())
            notify_data_changed(self)

    def _delete(self) -> None:
        did = self._selected_id()
        if not did:
            QMessageBox.information(self, "Seleção", "Selecione um documento para excluir.")
            return
        if QMessageBox.question(self, "Confirmar", "Excluir documento?") == QMessageBox.Yes:
            DocumentRepository.delete(did)
            notify_data_changed(self)
