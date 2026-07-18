from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QFileDialog,
    QComboBox,
)
from PySide6.QtCore import Qt

from motocontrol.config import BACKUP_DIR
from motocontrol.database.repositories import SettingsRepository
from motocontrol.services.backup import create_backup, list_backups, restore_backup
from motocontrol.ui.helpers import notify_data_changed, set_table_item


class SettingsPage(QWidget):
    theme_changed = None

    def __init__(self, on_theme_changed=None, parent=None):
        super().__init__(parent)
        self.on_theme_changed = on_theme_changed
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("Configurações e Backup")
        title.setObjectName("title")
        layout.addWidget(title)

        theme_group = QGroupBox("Aparência")
        theme_form = QFormLayout(theme_group)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark Mode", "dark")
        self.theme_combo.addItem("Light Mode", "light")
        self.theme_combo.currentIndexChanged.connect(self._save_theme)
        theme_form.addRow("Tema:", self.theme_combo)
        layout.addWidget(theme_group)

        backup_group = QGroupBox("Backup Automático")
        backup_form = QFormLayout(backup_group)
        self.chk_daily = QCheckBox("Backup diário")
        self.chk_weekly = QCheckBox("Backup semanal")
        self.chk_monthly = QCheckBox("Backup mensal")
        backup_form.addRow(self.chk_daily)
        backup_form.addRow(self.chk_weekly)
        backup_form.addRow(self.chk_monthly)
        btn_save_backup = QPushButton("Salvar Preferências de Backup")
        btn_save_backup.clicked.connect(self._save_backup_prefs)
        backup_form.addRow(btn_save_backup)
        layout.addWidget(backup_group)

        manual_group = QGroupBox("Backup Manual")
        manual_layout = QHBoxLayout(manual_group)
        btn_manual = QPushButton("Criar Backup Agora")
        btn_manual.clicked.connect(self._manual_backup)
        btn_restore = QPushButton("Restaurar Backup")
        btn_restore.setObjectName("secondaryBtn")
        btn_restore.clicked.connect(self._restore_backup)
        manual_layout.addWidget(btn_manual)
        manual_layout.addWidget(btn_restore)
        layout.addWidget(manual_group)

        layout.addWidget(QLabel("Backups disponíveis:"))
        self.backup_table = QTableWidget(0, 3)
        self.backup_table.setHorizontalHeaderLabels(["Arquivo", "Tamanho (KB)", "Criado"])
        bheader = self.backup_table.horizontalHeader()
        bheader.setSectionResizeMode(QHeaderView.ResizeToContents)
        bheader.setStretchLastSection(True)
        bheader.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.backup_table)

        info = QLabel(f"Pasta de backups: {BACKUP_DIR}")
        info.setObjectName("subtitle")
        info.setWordWrap(True)
        layout.addWidget(info)
        layout.addStretch()

    def refresh(self) -> None:
        theme = SettingsRepository.get("theme", "dark")
        idx = self.theme_combo.findData(theme)
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.theme_combo.blockSignals(False)

        self.chk_daily.setChecked(SettingsRepository.get("backup_daily", "1") == "1")
        self.chk_weekly.setChecked(SettingsRepository.get("backup_weekly", "1") == "1")
        self.chk_monthly.setChecked(SettingsRepository.get("backup_monthly", "1") == "1")

        backups = list_backups()
        self.backup_table.setRowCount(len(backups))
        for row, b in enumerate(backups):
            set_table_item(self.backup_table, row, 0, b["name"])
            set_table_item(self.backup_table, row, 1, str(b["size_kb"]))
            set_table_item(self.backup_table, row, 2, b["created"])

    def _save_theme(self) -> None:
        theme = self.theme_combo.currentData()
        SettingsRepository.set("theme", theme)
        if self.on_theme_changed:
            self.on_theme_changed(theme)

    def _save_backup_prefs(self) -> None:
        SettingsRepository.set("backup_daily", "1" if self.chk_daily.isChecked() else "0")
        SettingsRepository.set("backup_weekly", "1" if self.chk_weekly.isChecked() else "0")
        SettingsRepository.set("backup_monthly", "1" if self.chk_monthly.isChecked() else "0")
        QMessageBox.information(self, "Salvo", "Preferências de backup atualizadas.")

    def _manual_backup(self) -> None:
        path = create_backup("manual")
        QMessageBox.information(self, "Backup", f"Backup criado:\n{path}")
        self.refresh()

    def _restore_backup(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Backup",
            str(BACKUP_DIR),
            "Banco SQLite (*.db)",
        )
        if not path:
            return
        if QMessageBox.question(
            self,
            "Confirmar",
            "Restaurar backup? Os dados atuais serão substituídos.",
        ) != QMessageBox.Yes:
            return
        try:
            restore_backup(Path(path))
            QMessageBox.information(self, "Sucesso", "Backup restaurado com sucesso.")
            notify_data_changed(self)
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))
