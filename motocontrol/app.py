import sys

from PySide6.QtWidgets import QApplication

from motocontrol.config import APP_NAME
from motocontrol.database.db import init_db
from motocontrol.services.backup import run_scheduled_backups
from motocontrol.ui.main_window import MainWindow


def run() -> int:
    init_db()
    run_scheduled_backups()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    return app.exec()
