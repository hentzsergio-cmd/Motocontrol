from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from motocontrol.config import APP_NAME, APP_VERSION
from motocontrol.database.repositories import SettingsRepository, VehicleRepository
from motocontrol.services.calculations import get_document_alerts
from motocontrol.ui.pages.dashboard import DashboardPage
from motocontrol.ui.pages.documents import DocumentsPage
from motocontrol.ui.pages.financial import FinancialPage
from motocontrol.ui.pages.fuelings import FuelingsPage
from motocontrol.ui.pages.maintenance import MaintenancePage
from motocontrol.ui.pages.reports import ReportsPage
from motocontrol.ui.pages.settings import SettingsPage
from motocontrol.ui.pages.vehicles import VehiclesPage
from motocontrol.ui.theme import get_stylesheet


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._current_page_key = "dashboard"
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1280, 820)
        self.setMinimumSize(1024, 680)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = self._build_sidebar()
        root.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.pages = {
            "dashboard": DashboardPage(),
            "vehicles": VehiclesPage(),
            "fuelings": FuelingsPage(),
            "maintenance": MaintenancePage(),
            "documents": DocumentsPage(),
            "financial": FinancialPage(),
            "reports": ReportsPage(),
            "settings": SettingsPage(on_theme_changed=self.apply_theme),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)
        root.addWidget(self.stack, 1)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self._setup_shortcuts()
        self._restore_vehicle_filter()
        self.apply_theme(SettingsRepository.get("theme", "dark"))
        self.navigate("dashboard")

    def _build_sidebar(self) -> QFrame:
        self.nav_buttons: dict[str, QPushButton] = {}
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        logo = QLabel(APP_NAME)
        logo.setStyleSheet("font-size: 18px; font-weight: 700; padding: 8px 4px 20px 4px;")
        layout.addWidget(logo)

        nav_items = [
            ("dashboard", "Dashboard"),
            ("vehicles", "Veículos"),
            ("fuelings", "Abastecimentos"),
            ("maintenance", "Manutenções"),
            ("documents", "Documentação"),
            ("financial", "Financeiro"),
            ("reports", "Relatórios"),
            ("settings", "Configurações"),
        ]
        for key, label in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self.navigate(k))
            self.nav_buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()
        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("subtitle")
        layout.addWidget(version)
        return sidebar

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("F5"), self, self.refresh_all)
        QShortcut(QKeySequence("Ctrl+E"), self, self._edit_current_page)
        QShortcut(QKeySequence("Delete"), self, self._delete_current_page)

    def _edit_current_page(self) -> None:
        page = self.stack.currentWidget()
        if hasattr(page, "_edit"):
            page._edit()

    def _delete_current_page(self) -> None:
        page = self.stack.currentWidget()
        if hasattr(page, "_delete"):
            page._delete()

    def _restore_vehicle_filter(self) -> None:
        saved = SettingsRepository.get("last_vehicle_id", "")
        vehicle_id = int(saved) if saved.isdigit() else None
        for page in self.pages.values():
            if hasattr(page, "filter_bar"):
                page.filter_bar.set_vehicle_id(vehicle_id)

    def on_vehicle_filter_changed(self, vehicle_id: int | None) -> None:
        SettingsRepository.set("last_vehicle_id", str(vehicle_id) if vehicle_id else "")
        sender = self.sender()
        for page in self.pages.values():
            if hasattr(page, "filter_bar") and page.filter_bar is not sender:
                page.filter_bar.set_vehicle_id(vehicle_id)
        current = self.stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()
        self._update_status_message()

    def navigate(self, key: str) -> None:
        self._current_page_key = key
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)
        page = self.pages[key]
        self.stack.setCurrentWidget(page)
        if hasattr(page, "refresh"):
            page.refresh()
        self._update_status_message()
        self._update_document_badge()

    def _update_status_message(self) -> None:
        titles = {
            "dashboard": "Dashboard",
            "vehicles": "Veículos",
            "financial": "Financeiro",
            "fuelings": "Abastecimentos",
            "maintenance": "Manutenções",
            "documents": "Documentação",
            "reports": "Relatórios",
            "settings": "Configurações",
        }
        vehicle_count = len(VehicleRepository.list_all())
        alert_count = len(get_document_alerts())
        parts = [titles.get(self._current_page_key, "")]
        if vehicle_count == 0:
            parts.append("Cadastre seu primeiro veículo em Veículos")
        else:
            parts.append(f"{vehicle_count} veículo(s)")
            if alert_count:
                parts.append(f"{alert_count} alerta(s) de documento")
        self.status.showMessage(" · ".join(parts))

    def _update_document_badge(self) -> None:
        alert_count = len(get_document_alerts())
        btn = self.nav_buttons["documents"]
        btn.setText("Documentação" if alert_count == 0 else f"Documentação ({alert_count})")

    def apply_theme(self, theme: str) -> None:
        self.setStyleSheet(get_stylesheet(theme))

    def refresh_all(self) -> None:
        for page in self.pages.values():
            if hasattr(page, "refresh"):
                page.refresh()
        self._update_status_message()
        self._update_document_badge()
