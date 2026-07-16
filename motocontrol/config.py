from pathlib import Path

APP_NAME = "MOTOCONTROL PRO"
APP_VERSION = "1.1.0"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
DB_PATH = DATA_DIR / "motocontrol.db"

DOCUMENT_TYPES = ["IPVA", "Licenciamento", "Seguro", "CRLV", "Garantias"]
MAINTENANCE_CATEGORIES = [
    "Óleo",
    "Filtro",
    "Relação",
    "Pneus",
    "Pastilhas",
    "Fluido de Freio",
    "Revisão",
    "Outros",
]
FINANCIAL_CATEGORIES = [
    "Combustível",
    "Manutenção",
    "Seguro",
    "Documentação",
    "Acessórios",
    "Lavagens",
]
FUEL_TYPES = ["Gasolina", "Gasolina Aditivada", "Etanol", "Flex", "Diesel", "GNV"]
ALERT_DAYS = [60, 30, 15, 7]
DOCUMENT_ALERT_DAYS = ALERT_DAYS
REVISION_FIRST_KM = 1000
REVISION_INTERVAL_KM = 5000
