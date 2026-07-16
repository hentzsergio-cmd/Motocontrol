from typing import Any

from motocontrol.database.db import get_connection, row_to_dict, rows_to_list


class VehicleRepository:
    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM vehicles ORDER BY marca, modelo"
            ).fetchall()
            return rows_to_list(rows)

    @staticmethod
    def get(vehicle_id: int) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)
            ).fetchone()
            return row_to_dict(row)

    @staticmethod
    def create(data: dict[str, Any]) -> int:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO vehicles (marca, modelo, ano, placa, renavam, data_compra, valor_compra, capacidade_tanque)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["marca"],
                    data["modelo"],
                    data["ano"],
                    data["placa"].upper(),
                    data.get("renavam", ""),
                    data.get("data_compra", ""),
                    data.get("valor_compra", 0),
                    data.get("capacidade_tanque", 0),
                ),
            )
            return cur.lastrowid

    @staticmethod
    def update(vehicle_id: int, data: dict[str, Any]) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE vehicles SET marca=?, modelo=?, ano=?, placa=?, renavam=?,
                data_compra=?, valor_compra=?, capacidade_tanque=? WHERE id=?
                """,
                (
                    data["marca"],
                    data["modelo"],
                    data["ano"],
                    data["placa"].upper(),
                    data.get("renavam", ""),
                    data.get("data_compra", ""),
                    data.get("valor_compra", 0),
                    data.get("capacidade_tanque", 0),
                    vehicle_id,
                ),
            )

    @staticmethod
    def delete(vehicle_id: int) -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))


class FuelingRepository:
    @staticmethod
    def list_all(vehicle_id: int | None = None) -> list[dict[str, Any]]:
        with get_connection() as conn:
            if vehicle_id:
                rows = conn.execute(
                    """
                    SELECT f.*, v.placa, v.marca, v.modelo
                    FROM fuelings f JOIN vehicles v ON v.id = f.vehicle_id
                    WHERE f.vehicle_id = ? ORDER BY f.data DESC, f.quilometragem DESC
                    """,
                    (vehicle_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT f.*, v.placa, v.marca, v.modelo
                    FROM fuelings f JOIN vehicles v ON v.id = f.vehicle_id
                    ORDER BY f.data DESC, f.quilometragem DESC
                    """
                ).fetchall()
            return rows_to_list(rows)

    @staticmethod
    def create(data: dict[str, Any]) -> int:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO fuelings (vehicle_id, data, quilometragem, litros, valor, posto, tipo_combustivel, tanque_cheio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["vehicle_id"],
                    data["data"],
                    data["quilometragem"],
                    data["litros"],
                    data["valor"],
                    data.get("posto", ""),
                    data.get("tipo_combustivel", ""),
                    1 if data.get("tanque_cheio", True) else 0,
                ),
            )
            return cur.lastrowid

    @staticmethod
    def update(fueling_id: int, data: dict[str, Any]) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE fuelings SET vehicle_id=?, data=?, quilometragem=?, litros=?,
                valor=?, posto=?, tipo_combustivel=?, tanque_cheio=? WHERE id=?
                """,
                (
                    data["vehicle_id"],
                    data["data"],
                    data["quilometragem"],
                    data["litros"],
                    data["valor"],
                    data.get("posto", ""),
                    data.get("tipo_combustivel", ""),
                    1 if data.get("tanque_cheio", True) else 0,
                    fueling_id,
                ),
            )

    @staticmethod
    def delete(fueling_id: int) -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM fuelings WHERE id = ?", (fueling_id,))


class MaintenanceRepository:
    @staticmethod
    def list_all(vehicle_id: int | None = None) -> list[dict[str, Any]]:
        with get_connection() as conn:
            if vehicle_id:
                rows = conn.execute(
                    """
                    SELECT m.*, v.placa, v.marca, v.modelo
                    FROM maintenances m JOIN vehicles v ON v.id = m.vehicle_id
                    WHERE m.vehicle_id = ? ORDER BY m.data DESC
                    """,
                    (vehicle_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT m.*, v.placa, v.marca, v.modelo
                    FROM maintenances m JOIN vehicles v ON v.id = m.vehicle_id
                    ORDER BY m.data DESC
                    """
                ).fetchall()
            return rows_to_list(rows)

    @staticmethod
    def create(data: dict[str, Any]) -> int:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO maintenances (vehicle_id, data, quilometragem, categoria, descricao, oficina, valor)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["vehicle_id"],
                    data["data"],
                    data["quilometragem"],
                    data["categoria"],
                    data.get("descricao", ""),
                    data.get("oficina", ""),
                    data.get("valor", 0),
                ),
            )
            return cur.lastrowid

    @staticmethod
    def update(maintenance_id: int, data: dict[str, Any]) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE maintenances SET vehicle_id=?, data=?, quilometragem=?, categoria=?,
                descricao=?, oficina=?, valor=? WHERE id=?
                """,
                (
                    data["vehicle_id"],
                    data["data"],
                    data["quilometragem"],
                    data["categoria"],
                    data.get("descricao", ""),
                    data.get("oficina", ""),
                    data.get("valor", 0),
                    maintenance_id,
                ),
            )

    @staticmethod
    def delete(maintenance_id: int) -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM maintenances WHERE id = ?", (maintenance_id,))


class DocumentRepository:
    @staticmethod
    def list_all(vehicle_id: int | None = None) -> list[dict[str, Any]]:
        with get_connection() as conn:
            if vehicle_id:
                rows = conn.execute(
                    """
                    SELECT d.*, v.placa, v.marca, v.modelo
                    FROM documents d JOIN vehicles v ON v.id = d.vehicle_id
                    WHERE d.vehicle_id = ? ORDER BY d.data_vencimento ASC
                    """,
                    (vehicle_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT d.*, v.placa, v.marca, v.modelo
                    FROM documents d JOIN vehicles v ON v.id = d.vehicle_id
                    ORDER BY d.data_vencimento ASC
                    """
                ).fetchall()
            return rows_to_list(rows)

    @staticmethod
    def create(data: dict[str, Any]) -> int:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO documents (vehicle_id, tipo, descricao, data_vencimento, valor, observacao)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    data["vehicle_id"],
                    data["tipo"],
                    data.get("descricao", ""),
                    data["data_vencimento"],
                    data.get("valor", 0),
                    data.get("observacao", ""),
                ),
            )
            return cur.lastrowid

    @staticmethod
    def update(document_id: int, data: dict[str, Any]) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE documents SET vehicle_id=?, tipo=?, descricao=?, data_vencimento=?,
                valor=?, observacao=? WHERE id=?
                """,
                (
                    data["vehicle_id"],
                    data["tipo"],
                    data.get("descricao", ""),
                    data["data_vencimento"],
                    data.get("valor", 0),
                    data.get("observacao", ""),
                    document_id,
                ),
            )

    @staticmethod
    def delete(document_id: int) -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))


class FinancialRepository:
    @staticmethod
    def list_all(vehicle_id: int | None = None) -> list[dict[str, Any]]:
        with get_connection() as conn:
            if vehicle_id:
                rows = conn.execute(
                    """
                    SELECT f.*, v.placa, v.marca, v.modelo
                    FROM financial_entries f LEFT JOIN vehicles v ON v.id = f.vehicle_id
                    WHERE f.vehicle_id = ? ORDER BY f.data DESC
                    """,
                    (vehicle_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT f.*, v.placa, v.marca, v.modelo
                    FROM financial_entries f LEFT JOIN vehicles v ON v.id = f.vehicle_id
                    ORDER BY f.data DESC
                    """
                ).fetchall()
            return rows_to_list(rows)

    @staticmethod
    def create(data: dict[str, Any]) -> int:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO financial_entries (vehicle_id, data, categoria, descricao, valor)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    data.get("vehicle_id"),
                    data["data"],
                    data["categoria"],
                    data.get("descricao", ""),
                    data["valor"],
                ),
            )
            return cur.lastrowid

    @staticmethod
    def update(entry_id: int, data: dict[str, Any]) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE financial_entries SET vehicle_id=?, data=?, categoria=?, descricao=?, valor=?
                WHERE id=?
                """,
                (
                    data.get("vehicle_id"),
                    data["data"],
                    data["categoria"],
                    data.get("descricao", ""),
                    data["valor"],
                    entry_id,
                ),
            )

    @staticmethod
    def delete(entry_id: int) -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM financial_entries WHERE id = ?", (entry_id,))


class SettingsRepository:
    @staticmethod
    def get(key: str, default: str = "") -> str:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    @staticmethod
    def set(key: str, value: str) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (key, value),
            )

    @staticmethod
    def get_all() -> dict[str, str]:
        with get_connection() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            return {r["key"]: r["value"] for r in rows}
