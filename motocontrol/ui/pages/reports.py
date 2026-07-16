from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from motocontrol.services.reports import generate_report
from motocontrol.ui.widgets.cards import VehicleFilterBar

REPORT_TYPES = [
    ("historico", "Histórico Completo"),
    ("financeiro_mensal", "Financeiro Mensal"),
    ("financeiro_anual", "Financeiro Anual"),
    ("consumo", "Consumo"),
    ("manutencoes", "Manutenções"),
    ("documentos", "Documentação e Alertas"),
]

FORMATS = [("pdf", "PDF"), ("xlsx", "Excel (XLSX)"), ("csv", "CSV")]


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("Relatórios")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("Exporte relatórios em PDF, XLSX ou CSV")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        group = QGroupBox("Gerar Relatório")
        form = QFormLayout(group)
        self.filter_bar = VehicleFilterBar()
        self.report_type = QComboBox()
        for key, label in REPORT_TYPES:
            self.report_type.addItem(label, key)
        self.format_combo = QComboBox()
        for key, label in FORMATS:
            self.format_combo.addItem(label, key)
        form.addRow("Veículo:", self.filter_bar)
        form.addRow("Relatório:", self.report_type)
        form.addRow("Formato:", self.format_combo)
        layout.addWidget(group)

        btn_export = QPushButton("Exportar Relatório")
        btn_export.clicked.connect(self._export)
        layout.addWidget(btn_export)
        layout.addStretch()

    def refresh(self) -> None:
        self.filter_bar.refresh()

    def _export(self) -> None:
        report_type = self.report_type.currentData()
        fmt = self.format_combo.currentData()
        ext = {"pdf": "pdf", "xlsx": "xlsx", "csv": "csv"}[fmt]
        default_name = f"motocontrol_{report_type}.{ext}"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Relatório",
            default_name,
            f"Arquivo *.{ext}",
        )
        if not path:
            return
        try:
            generate_report(
                report_type,
                fmt,
                Path(path),
                self.filter_bar.selected_vehicle_id(),
            )
            QMessageBox.information(self, "Sucesso", f"Relatório salvo em:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao gerar relatório:\n{exc}")
