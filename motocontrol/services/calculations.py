from datetime import datetime, timedelta
from typing import Any

from motocontrol.config import DOCUMENT_ALERT_DAYS, REVISION_FIRST_KM, REVISION_INTERVAL_KM
from motocontrol.database.repositories import (
    DocumentRepository,
    FinancialRepository,
    FuelingRepository,
    MaintenanceRepository,
    VehicleRepository,
)


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value[:10], fmt)
        except ValueError:
            continue
    return None


def _month_key(value: str) -> str:
    dt = _parse_date(value)
    return dt.strftime("%Y-%m") if dt else ""


def _year_key(value: str) -> str:
    dt = _parse_date(value)
    return dt.strftime("%Y") if dt else ""


def _current_month() -> str:
    return datetime.now().strftime("%Y-%m")


def _current_year() -> str:
    return datetime.now().strftime("%Y")


def _all_fueling_odometer_points(vehicle_id: int) -> list[tuple[str, float]]:
    points: list[tuple[str, float]] = []
    for fueling in FuelingRepository.list_all(vehicle_id):
        points.append((fueling["data"], fueling["quilometragem"]))
    return sorted(points, key=lambda p: (p[0], p[1]))


def _fueling_odometer_points(vehicle_id: int) -> list[tuple[str, float]]:
    points: list[tuple[str, float]] = []
    for fueling in FuelingRepository.list_all(vehicle_id):
        if fueling["quilometragem"] > 0:
            points.append((fueling["data"], fueling["quilometragem"]))
    return sorted(points, key=lambda p: (p[0], p[1]))


def _odometer_points(vehicle_id: int) -> list[tuple[str, float]]:
    """Quilometragem real vem dos abastecimentos, não de lançamentos de manutenção."""
    return _fueling_odometer_points(vehicle_id)


def compute_fueling_consumption(
    fuelings: list[dict[str, Any]],
    maintenances: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    maintenances = maintenances or []
    sorted_fuelings = sorted(
        fuelings,
        key=lambda f: (f["vehicle_id"], f["data"], f["quilometragem"]),
    )
    results: list[dict[str, Any]] = []
    prev_by_vehicle: dict[int, dict[str, Any]] = {}

    for vehicle_id in {f["vehicle_id"] for f in sorted_fuelings}:
        vehicle_fuelings = [
            f for f in sorted_fuelings if f["vehicle_id"] == vehicle_id
        ]
        if not vehicle_fuelings:
            continue
        first_date = vehicle_fuelings[0]["data"]
        prior_maintenances = [
            m
            for m in maintenances
            if m["vehicle_id"] == vehicle_id
            and m["data"] <= first_date
            and m["categoria"] != "Revisão"
            and m["quilometragem"] > 0
        ]
        if prior_maintenances:
            prev_by_vehicle[vehicle_id] = max(
                prior_maintenances,
                key=lambda m: (m["quilometragem"], m["data"]),
            )

    for fuel in sorted_fuelings:
        entry = dict(fuel)
        entry["km_l"] = None
        entry["custo_km"] = None
        prev = prev_by_vehicle.get(fuel["vehicle_id"])
        is_full = bool(fuel.get("tanque_cheio", 1))
        if prev and is_full:
            km_diff = fuel["quilometragem"] - prev["quilometragem"]
            if km_diff > 0 and fuel["litros"] > 0:
                entry["km_l"] = round(km_diff / fuel["litros"], 2)
                entry["custo_km"] = round(fuel["valor"] / km_diff, 4)
        if is_full:
            prev_by_vehicle[fuel["vehicle_id"]] = fuel
        results.append(entry)
    return results


def _positive_odometer_values(values: list[float]) -> list[float]:
    positive = [v for v in values if v > 0]
    return positive if positive else values


def get_latest_odometer(vehicle_id: int | None = None) -> float:
    if vehicle_id is None:
        vehicles = VehicleRepository.list_all()
        if not vehicles:
            return 0.0
        return sum(get_latest_odometer(v["id"]) for v in vehicles)

    fuelings = _fueling_odometer_points(vehicle_id)
    if fuelings:
        return fuelings[-1][1]

    maintenances = MaintenanceRepository.list_all(vehicle_id)
    non_revision = [
        m["quilometragem"]
        for m in maintenances
        if m["quilometragem"] > 0 and m["categoria"] != "Revisão"
    ]
    if non_revision:
        return max(non_revision)

    return 0.0


def get_monthly_km(vehicle_id: int | None = None) -> float:
    if vehicle_id is None:
        vehicles = VehicleRepository.list_all()
        return sum(get_monthly_km(v["id"]) for v in vehicles)

    month = _current_month()
    points = _all_fueling_odometer_points(vehicle_id)
    month_points = [p for p in points if _month_key(p[0]) == month]
    if not month_points:
        return 0.0

    month_vals = [p[1] for p in month_points]
    max_in_month = max(month_vals)
    prior_points = [p for p in points if _month_key(p[0]) < month]
    if prior_points:
        baseline = max(p[1] for p in prior_points)
        return max(0.0, max_in_month - baseline)

    if len(month_vals) >= 2:
        return max(month_vals) - min(month_vals)

    if len(month_vals) == 1 and month_vals[0] > 0:
        return month_vals[0]
    return 0.0


def _tank_capacity(vehicle_id: int | None = None) -> float:
    if vehicle_id:
        vehicle = VehicleRepository.get(vehicle_id)
        capacity = (vehicle or {}).get("capacidade_tanque") or 0
        if capacity > 0:
            return capacity

    full_fuelings = [
        f
        for f in FuelingRepository.list_all(vehicle_id)
        if f.get("tanque_cheio", 1) and f["litros"] > 0
    ]
    return full_fuelings[0]["litros"] if full_fuelings else 0.0


def get_consumption_stats(vehicle_id: int | None = None) -> dict[str, float | None]:
    fuelings = compute_fueling_consumption(
        FuelingRepository.list_all(vehicle_id),
        MaintenanceRepository.list_all(vehicle_id),
    )
    km_l_values = [f["km_l"] for f in fuelings if f["km_l"]]
    if not km_l_values:
        return {"media": None, "maximo": None, "minimo": None, "autonomia": None}

    media = sum(km_l_values) / len(km_l_values)
    tank_estimate = _tank_capacity(vehicle_id)
    autonomia = media * tank_estimate if tank_estimate else None

    maximo = round(max(km_l_values), 2)
    minimo = round(min(km_l_values), 2)

    return {
        "media": round(media, 2),
        "maximo": maximo,
        "minimo": minimo,
        "autonomia": round(autonomia, 1) if autonomia else None,
    }


def get_total_spent(
    vehicle_id: int | None = None,
    period: str = "all",
) -> float:
    total = 0.0
    fuelings = FuelingRepository.list_all(vehicle_id)
    maintenances = MaintenanceRepository.list_all(vehicle_id)
    documents = DocumentRepository.list_all(vehicle_id)
    financial = FinancialRepository.list_all(vehicle_id)

    month = _current_month()
    year = _current_year()

    def in_period(date_str: str) -> bool:
        if period == "month":
            return _month_key(date_str) == month
        if period == "year":
            return _year_key(date_str) == year
        return True

    tracked_in_modules = {"Combustível", "Manutenção", "Documentação"}

    for f in fuelings:
        if in_period(f["data"]):
            total += f["valor"]
    for m in maintenances:
        if in_period(m["data"]):
            total += m["valor"]
    for d in documents:
        if in_period(d["data_vencimento"]):
            total += d["valor"]
    for e in financial:
        if e["categoria"] in tracked_in_modules:
            continue
        if in_period(e["data"]):
            total += e["valor"]
    return round(total, 2)


def get_total_invested(vehicle_id: int | None = None) -> float:
    vehicles = VehicleRepository.list_all()
    if vehicle_id:
        vehicles = [v for v in vehicles if v["id"] == vehicle_id]

    purchase = sum(v.get("valor_compra") or 0 for v in vehicles)
    spent = get_total_spent(vehicle_id, "all")
    return round(purchase + spent, 2)


def get_cost_per_km(vehicle_id: int | None = None) -> float | None:
    odometer = get_latest_odometer(vehicle_id)
    if odometer <= 0:
        return None
    total = get_total_spent(vehicle_id, "all")
    return round(total / odometer, 4)


def get_next_maintenance(vehicle_id: int | None = None) -> dict[str, Any] | None:
    current = get_latest_odometer(vehicle_id)
    maintenances = MaintenanceRepository.list_all(vehicle_id)
    revisoes = [m for m in maintenances if m["categoria"] == "Revisão"]

    milestones = sorted(
        {m["quilometragem"] for m in revisoes if m["quilometragem"] > 0}
    )
    if milestones:
        highest_recorded = max(milestones)
        if current < highest_recorded:
            proxima_km = highest_recorded
        else:
            proxima_km = highest_recorded + REVISION_INTERVAL_KM
            while proxima_km <= current:
                proxima_km += REVISION_INTERVAL_KM
        latest = max(revisoes, key=lambda m: m["data"])
        ultima_km = latest["quilometragem"]
        data_ultima = latest["data"]
    else:
        proxima_km = REVISION_FIRST_KM
        ultima_km = 0.0
        data_ultima = None

    return {
        "ultima_revisao_km": round(ultima_km, 1),
        "proxima_revisao_km": round(proxima_km, 1),
        "faltam_km": max(0, round(proxima_km - current, 1)),
        "data_ultima": data_ultima,
    }


def get_next_document(vehicle_id: int | None = None) -> dict[str, Any] | None:
    documents = DocumentRepository.list_all(vehicle_id)
    today = datetime.now().date()
    upcoming = []
    for doc in documents:
        dt = _parse_date(doc["data_vencimento"])
        if dt:
            days = (dt.date() - today).days
            upcoming.append({**doc, "dias_restantes": days})
    if not upcoming:
        return None
    return min(upcoming, key=lambda d: d["dias_restantes"])


def get_document_alerts(vehicle_id: int | None = None) -> list[dict[str, Any]]:
    documents = DocumentRepository.list_all(vehicle_id)
    today = datetime.now().date()
    alerts = []
    for doc in documents:
        dt = _parse_date(doc["data_vencimento"])
        if not dt:
            continue
        days = (dt.date() - today).days
        if days <= max(DOCUMENT_ALERT_DAYS) or days < 0:
            alerts.append({**doc, "dias_restantes": days})
    return sorted(alerts, key=lambda d: d["dias_restantes"])


def get_dashboard_data(vehicle_id: int | None = None) -> dict[str, Any]:
    consumption = get_consumption_stats(vehicle_id)
    next_doc = get_next_document(vehicle_id)
    next_maint = get_next_maintenance(vehicle_id)

    return {
        "km_atual": get_latest_odometer(vehicle_id),
        "km_mes": get_monthly_km(vehicle_id),
        "consumo_medio": consumption["media"],
        "consumo_maximo": consumption["maximo"],
        "consumo_minimo": consumption["minimo"],
        "autonomia": consumption["autonomia"],
        "gasto_mensal": get_total_spent(vehicle_id, "month"),
        "gasto_anual": get_total_spent(vehicle_id, "year"),
        "total_investido": get_total_invested(vehicle_id),
        "custo_km": get_cost_per_km(vehicle_id),
        "proxima_revisao": next_maint,
        "proximo_documento": next_doc,
        "alertas_documentos": get_document_alerts(vehicle_id),
    }


def _format_month_label(month_key: str) -> str:
    dt = _parse_date(f"{month_key}-01")
    if not dt:
        return month_key
    months = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")
    return f"{months[dt.month - 1]}/{dt.strftime('%y')}"


def get_monthly_consumption_chart(vehicle_id: int | None = None) -> dict[str, list]:
    fuelings = compute_fueling_consumption(
        FuelingRepository.list_all(vehicle_id),
        MaintenanceRepository.list_all(vehicle_id),
    )
    months: dict[str, list[float]] = {}
    for f in fuelings:
        if f["km_l"]:
            key = _month_key(f["data"])
            months.setdefault(key, []).append(f["km_l"])
    keys = sorted(months.keys())[-12:]
    labels = [_format_month_label(k) for k in keys]
    values = [round(sum(months[m]) / len(months[m]), 2) for m in keys]
    return {"labels": labels, "values": values}


def get_odometer_evolution(vehicle_id: int | None = None) -> dict[str, list]:
    points = _fueling_odometer_points(vehicle_id) if vehicle_id else []
    if vehicle_id is None:
        points = []
        for vehicle in VehicleRepository.list_all():
            points.extend(_fueling_odometer_points(vehicle["id"]))
        points.sort(key=lambda p: (p[0], p[1]))
    return {"labels": [p[0] for p in points], "values": [p[1] for p in points]}


def get_monthly_spending_chart(vehicle_id: int | None = None) -> dict[str, list]:
    tracked_in_modules = {"Combustível", "Manutenção", "Documentação"}
    months: dict[str, float] = {}

    for f in FuelingRepository.list_all(vehicle_id):
        key = _month_key(f["data"])
        if key:
            months[key] = months.get(key, 0) + f["valor"]
    for m in MaintenanceRepository.list_all(vehicle_id):
        key = _month_key(m["data"])
        if key:
            months[key] = months.get(key, 0) + m["valor"]
    for d in DocumentRepository.list_all(vehicle_id):
        key = _month_key(d["data_vencimento"])
        if key:
            months[key] = months.get(key, 0) + d["valor"]
    for e in FinancialRepository.list_all(vehicle_id):
        if e["categoria"] in tracked_in_modules:
            continue
        key = _month_key(e["data"])
        if key:
            months[key] = months.get(key, 0) + e["valor"]

    keys = sorted(months.keys())[-12:]
    labels = [_format_month_label(k) for k in keys]
    values = [round(months[m], 2) for m in keys]
    return {"labels": labels, "values": values}


def get_cost_distribution(vehicle_id: int | None = None) -> dict[str, list]:
    categories = {
        "Combustível": 0.0,
        "Manutenção": 0.0,
        "Documentação": 0.0,
        "Seguro": 0.0,
        "Acessórios": 0.0,
        "Lavagens": 0.0,
        "Outros": 0.0,
    }
    tracked_in_modules = {"Combustível", "Manutenção", "Documentação"}
    for f in FuelingRepository.list_all(vehicle_id):
        categories["Combustível"] += f["valor"]
    for m in MaintenanceRepository.list_all(vehicle_id):
        categories["Manutenção"] += m["valor"]
    for d in DocumentRepository.list_all(vehicle_id):
        categories["Documentação"] += d["valor"]
    for e in FinancialRepository.list_all(vehicle_id):
        cat = e["categoria"]
        if cat in tracked_in_modules:
            continue
        if cat in categories:
            categories[cat] += e["valor"]
        else:
            categories["Outros"] += e["valor"]
    labels = [k for k, v in categories.items() if v > 0]
    values = [round(categories[k], 2) for k in labels]
    return {"labels": labels, "values": values}


def get_maintenance_history_chart(vehicle_id: int | None = None) -> dict[str, list]:
    maintenances = MaintenanceRepository.list_all(vehicle_id)
    counts: dict[str, int] = {}
    for m in maintenances:
        counts[m["categoria"]] = counts.get(m["categoria"], 0) + 1
    return {"labels": list(counts.keys()), "values": list(counts.values())}


def get_financial_summary(vehicle_id: int | None = None) -> dict[str, Any]:
    return {
        "gasto_mensal": get_total_spent(vehicle_id, "month"),
        "gasto_anual": get_total_spent(vehicle_id, "year"),
        "custo_km": get_cost_per_km(vehicle_id),
        "total_investido": get_total_invested(vehicle_id),
    }
