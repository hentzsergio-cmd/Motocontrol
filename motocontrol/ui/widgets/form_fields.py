from PySide6.QtCore import QDate
from PySide6.QtWidgets import QComboBox, QDateEdit, QDoubleSpinBox, QFormLayout, QLineEdit, QSpinBox, QWidget


def line_edit(placeholder: str = "") -> QLineEdit:
    field = QLineEdit()
    field.setPlaceholderText(placeholder)
    return field


def combo_box(items: list[str]) -> QComboBox:
    box = QComboBox()
    box.addItems(items)
    return box


def date_edit() -> QDateEdit:
    field = QDateEdit()
    field.setCalendarPopup(True)
    field.setDate(QDate.currentDate())
    field.setDisplayFormat("dd/MM/yyyy")
    return field


def money_spin(max_value: float = 9999999.99) -> QDoubleSpinBox:
    field = QDoubleSpinBox()
    field.setRange(0, max_value)
    field.setDecimals(2)
    field.setPrefix("R$ ")
    return field


def km_spin() -> QDoubleSpinBox:
    field = QDoubleSpinBox()
    field.setRange(0, 9999999)
    field.setDecimals(1)
    field.setSuffix(" km")
    return field


def liters_spin() -> QDoubleSpinBox:
    field = QDoubleSpinBox()
    field.setRange(0, 9999)
    field.setDecimals(2)
    field.setSuffix(" L")
    return field


def year_spin() -> QSpinBox:
    field = QSpinBox()
    field.setRange(1950, 2100)
    field.setValue(QDate.currentDate().year())
    return field


def vehicle_combo(vehicles: list[dict]) -> QComboBox:
    box = QComboBox()
    for vehicle in vehicles:
        label = f"{vehicle['placa']} - {vehicle['marca']} {vehicle['modelo']}"
        box.addItem(label, vehicle["id"])
    return box


def form_layout() -> QFormLayout:
    layout = QFormLayout()
    layout.setSpacing(10)
    return layout


def qdate_to_iso(field: QDateEdit) -> str:
    return field.date().toString("yyyy-MM-dd")


def iso_to_qdate(value: str, field: QDateEdit) -> None:
    if value:
        parts = value.split("-")
        if len(parts) == 3:
            field.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
