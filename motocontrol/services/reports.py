from pathlib import Path
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from motocontrol.database.repositories import (
    DocumentRepository,
    FinancialRepository,
    FuelingRepository,
    MaintenanceRepository,
    VehicleRepository,
)
from motocontrol.services.calculations import (
    compute_fueling_consumption,
    get_document_alerts,
    get_financial_summary,
    get_total_spent,
)


def _vehicles_df(vehicle_id: int | None = None) -> pd.DataFrame:
    vehicles = VehicleRepository.list_all()
    if vehicle_id:
        vehicles = [v for v in vehicles if v["id"] == vehicle_id]
    return pd.DataFrame(vehicles)


def _fuelings_df(vehicle_id: int | None = None) -> pd.DataFrame:
    fuelings = compute_fueling_consumption(
        FuelingRepository.list_all(vehicle_id),
        MaintenanceRepository.list_all(vehicle_id),
    )
    return pd.DataFrame(fuelings)


def _maintenances_df(vehicle_id: int | None = None) -> pd.DataFrame:
    return pd.DataFrame(MaintenanceRepository.list_all(vehicle_id))


def _documents_df(vehicle_id: int | None = None) -> pd.DataFrame:
    return pd.DataFrame(DocumentRepository.list_all(vehicle_id))


def _financial_df(vehicle_id: int | None = None) -> pd.DataFrame:
    return pd.DataFrame(FinancialRepository.list_all(vehicle_id))


def _documents_alert_df(vehicle_id: int | None = None) -> pd.DataFrame:
    return pd.DataFrame(get_document_alerts(vehicle_id))


def export_csv(report_type: str, path: Path, vehicle_id: int | None = None) -> None:
    frames = {
        "historico": _build_historico_frames(vehicle_id),
        "financeiro_mensal": _build_financeiro_mensal(vehicle_id),
        "financeiro_anual": _build_financeiro_anual(vehicle_id),
        "consumo": {"Consumo": _fuelings_df(vehicle_id)},
        "manutencoes": {"Manutenções": _maintenances_df(vehicle_id)},
        "documentos": {
            "Documentação": _documents_df(vehicle_id),
            "Alertas": _documents_alert_df(vehicle_id),
        },
    }
    data = frames.get(report_type, frames["historico"])
    if len(data) == 1:
        next(iter(data.values())).to_csv(path, index=False, encoding="utf-8-sig")
    else:
        combined = pd.concat(
            [df.assign(_secao=name) for name, df in data.items()],
            ignore_index=True,
        )
        combined.to_csv(path, index=False, encoding="utf-8-sig")


def export_xlsx(report_type: str, path: Path, vehicle_id: int | None = None) -> None:
    frames = {
        "historico": _build_historico_frames(vehicle_id),
        "financeiro_mensal": _build_financeiro_mensal(vehicle_id),
        "financeiro_anual": _build_financeiro_anual(vehicle_id),
        "consumo": {"Consumo": _fuelings_df(vehicle_id)},
        "manutencoes": {"Manutenções": _maintenances_df(vehicle_id)},
        "documentos": {
            "Documentação": _documents_df(vehicle_id),
            "Alertas": _documents_alert_df(vehicle_id),
        },
    }
    data = frames.get(report_type, frames["historico"])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, df in data.items():
            safe_name = sheet[:31]
            df.to_excel(writer, sheet_name=safe_name, index=False)


def export_pdf(report_type: str, path: Path, vehicle_id: int | None = None) -> None:
    titles = {
        "historico": "Histórico Completo",
        "financeiro_mensal": "Financeiro Mensal",
        "financeiro_anual": "Financeiro Anual",
        "consumo": "Relatório de Consumo",
        "manutencoes": "Relatório de Manutenções",
        "documentos": "Documentação e Alertas",
    }
    title = titles.get(report_type, "Relatório MOTOCONTROL PRO")

    if report_type == "historico":
        sections = _build_historico_frames(vehicle_id)
    elif report_type == "financeiro_mensal":
        sections = _build_financeiro_mensal(vehicle_id)
    elif report_type == "financeiro_anual":
        sections = _build_financeiro_anual(vehicle_id)
    elif report_type == "consumo":
        sections = {"Consumo": _fuelings_df(vehicle_id)}
    elif report_type == "manutencoes":
        sections = {"Manutenções": _maintenances_df(vehicle_id)}
    elif report_type == "documentos":
        sections = {
            "Documentação": _documents_df(vehicle_id),
            "Alertas": _documents_alert_df(vehicle_id),
        }
    else:
        sections = _build_historico_frames(vehicle_id)

    doc = SimpleDocTemplate(str(path), pagesize=A4)
    styles = getSampleStyleSheet()
    heading = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1a73e8"),
        spaceAfter=12,
    )
    story = [Paragraph(f"MOTOCONTROL PRO — {title}", styles["Title"]), Spacer(1, 0.5 * cm)]

    for section_name, df in sections.items():
        story.append(Paragraph(section_name, heading))
        if df.empty:
            story.append(Paragraph("Sem registros.", styles["Normal"]))
        else:
            table_data = [list(df.columns)] + df.astype(str).values.tolist()
            table = Table(table_data, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a73e8")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                    ]
                )
            )
            story.append(table)
        story.append(Spacer(1, 0.4 * cm))

    doc.build(story)


def _build_historico_frames(vehicle_id: int | None = None) -> dict[str, pd.DataFrame]:
    return {
        "Veículos": _vehicles_df(vehicle_id),
        "Abastecimentos": _fuelings_df(vehicle_id),
        "Manutenções": _maintenances_df(vehicle_id),
        "Documentação": _documents_df(vehicle_id),
        "Financeiro": _financial_df(vehicle_id),
    }


def _build_financeiro_mensal(vehicle_id: int | None = None) -> dict[str, pd.DataFrame]:
    summary = get_financial_summary(vehicle_id)
    df = pd.DataFrame([summary])
    df.columns = ["Gasto Mensal", "Gasto Anual", "Custo/KM", "Total Investido"]
    entries = _financial_df(vehicle_id)
    return {"Resumo": df, "Lançamentos": entries}


def _build_financeiro_anual(vehicle_id: int | None = None) -> dict[str, pd.DataFrame]:
    total = get_total_spent(vehicle_id, "year")
    df = pd.DataFrame([{"Gasto Anual": total}])
    return {"Resumo Anual": df, "Lançamentos": _financial_df(vehicle_id)}


def generate_report(
    report_type: str,
    fmt: str,
    path: Path,
    vehicle_id: int | None = None,
) -> None:
    fmt = fmt.lower()
    if fmt == "pdf":
        export_pdf(report_type, path, vehicle_id)
    elif fmt in ("xlsx", "excel"):
        export_xlsx(report_type, path, vehicle_id)
    elif fmt == "csv":
        export_csv(report_type, path, vehicle_id)
    else:
        raise ValueError(f"Formato não suportado: {fmt}")
