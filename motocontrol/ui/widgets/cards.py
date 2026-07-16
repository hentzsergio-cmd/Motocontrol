from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from motocontrol.database.repositories import VehicleRepository


class StatCard(QFrame):
    def __init__(self, label: str, value: str = "-", tooltip: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        self.title_label = QLabel(label)
        self.title_label.setObjectName("statLabel")
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)
        if tooltip:
            self.setToolTip(tooltip)
            self.value_label.setToolTip(tooltip)
            self.title_label.setToolTip(tooltip)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class VehicleFilterBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QComboBox, QHBoxLayout

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Veículo:"))
        self.combo = QComboBox()
        self.combo.addItem("Todos os veículos", None)
        layout.addWidget(self.combo, 1)
        self.combo.currentIndexChanged.connect(self._emit_change)
        self.refresh()

    def _emit_change(self) -> None:
        window = self.window()
        if hasattr(window, "on_vehicle_filter_changed"):
            window.on_vehicle_filter_changed(self.selected_vehicle_id())

    def set_vehicle_id(self, vehicle_id: int | None) -> None:
        self.combo.blockSignals(True)
        idx = self.combo.findData(vehicle_id)
        self.combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo.blockSignals(False)

    def refresh(self) -> None:
        current = self.combo.currentData()
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItem("Todos os veículos", None)
        for v in VehicleRepository.list_all():
            label = f"{v['marca']} {v['modelo']} — {v['placa']}"
            self.combo.addItem(label, v["id"])
        idx = self.combo.findData(current)
        self.combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo.blockSignals(False)

    def selected_vehicle_id(self) -> int | None:
        return self.combo.currentData()
