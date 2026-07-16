from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from motocontrol.database.repositories import VehicleRepository
from motocontrol.services.calculations import (
    get_cost_distribution,
    get_dashboard_data,
    get_maintenance_history_chart,
    get_monthly_consumption_chart,
    get_monthly_spending_chart,
    get_odometer_evolution,
)
from motocontrol.ui.helpers import (
    format_autonomia,
    format_consumption,
    format_currency,
    format_custo_km,
    format_date,
    format_document_countdown,
    format_km,
)
from motocontrol.ui.widgets.cards import StatCard, VehicleFilterBar
from motocontrol.ui.widgets.charts import ChartWidget


class DashboardPage(QWidget):
    CARD_TOOLTIPS = {
        "km_atual": "Quilometragem do último abastecimento registrado (hodômetro real).",
        "km_mes": "Quilômetros percorridos no mês com base na evolução do hodômetro.",
        "consumo_medio": "Média de KM/L calculada apenas em abastecimentos com tanque cheio.",
        "consumo_maximo": "Melhor consumo registrado entre abastecimentos completos.",
        "consumo_minimo": "Menor consumo registrado entre abastecimentos completos.",
        "autonomia": "Consumo médio multiplicado pela capacidade do tanque cadastrada.",
        "gasto_mensal": "Soma de abastecimentos, manutenções, documentos e lançamentos extras do mês.",
        "gasto_anual": "Soma de todos os custos registrados no ano corrente.",
        "total_investido": "Valor de compra dos veículos mais todos os custos registrados.",
        "custo_km": "Custo total acumulado dividido pela quilometragem atual.",
        "proxima_revisao": "Quilometragem do hodômetro na próxima revisão programada.",
        "proximo_documento": "Documento com vencimento mais próximo.",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("title")
        subtitle = QLabel("Visão geral da sua frota")
        subtitle.setObjectName("subtitle")
        title_box = QVBoxLayout()
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        self.filter_bar = VehicleFilterBar()
        header.addWidget(self.filter_bar)
        outer.addLayout(header)

        self.empty_state = QLabel("")
        self.empty_state.setObjectName("subtitle")
        self.empty_state.setWordWrap(True)
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self.empty_state)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.dashboard_content = QWidget()
        self.content_layout = QVBoxLayout(self.dashboard_content)

        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(12)
        labels = {
            "km_atual": "KM Atual",
            "km_mes": "KM Rodados no Mês",
            "consumo_medio": "Consumo Médio (KM/L)",
            "consumo_maximo": "Consumo Máximo",
            "consumo_minimo": "Consumo Mínimo",
            "autonomia": "Autonomia Estimada (KM)",
            "gasto_mensal": "Gasto Mensal (R$)",
            "gasto_anual": "Gasto Anual (R$)",
            "total_investido": "Total Investido (R$)",
            "custo_km": "Custo por KM (R$)",
            "proxima_revisao": "Próxima Revisão",
            "proximo_documento": "Próximo Documento",
        }
        self.stat_cards = {
            key: StatCard(label, tooltip=self.CARD_TOOLTIPS[key])
            for key, label in labels.items()
        }
        for i, card in enumerate(self.stat_cards.values()):
            self.stats_grid.addWidget(card, i // 4, i % 4)
        self.content_layout.addLayout(self.stats_grid)

        self.alert_label = QLabel("")
        self.alert_label.setObjectName("alert")
        self.alert_label.setWordWrap(True)
        self.content_layout.addWidget(self.alert_label)

        alert_actions = QHBoxLayout()
        self.btn_view_documents = QPushButton("Ver documentos")
        self.btn_view_documents.setObjectName("secondaryBtn")
        self.btn_view_documents.clicked.connect(self._open_documents)
        self.btn_view_documents.hide()
        alert_actions.addWidget(self.btn_view_documents)
        alert_actions.addStretch()
        self.content_layout.addLayout(alert_actions)

        charts_grid = QGridLayout()
        charts_grid.setSpacing(12)
        self.chart_consumo = ChartWidget("Consumo Mensal (KM/L)", "bar")
        self.chart_km = ChartWidget("Evolução da Quilometragem", "line")
        self.chart_gastos = ChartWidget("Gastos Mensais (R$)", "bar")
        self.chart_distribuicao = ChartWidget("Distribuição dos Custos", "pie")
        self.chart_manutencao = ChartWidget("Histórico de Manutenções", "bar")
        charts_grid.addWidget(self.chart_consumo, 0, 0)
        charts_grid.addWidget(self.chart_km, 0, 1)
        charts_grid.addWidget(self.chart_gastos, 1, 0)
        charts_grid.addWidget(self.chart_distribuicao, 1, 1)
        charts_grid.addWidget(self.chart_manutencao, 2, 0, 1, 2)
        self.content_layout.addLayout(charts_grid)

        scroll.setWidget(self.dashboard_content)
        outer.addWidget(scroll)

    def _open_documents(self) -> None:
        window = self.window()
        if hasattr(window, "navigate"):
            window.navigate("documents")

    def refresh(self) -> None:
        self.filter_bar.refresh()
        if not VehicleRepository.list_all():
            self.empty_state.setText(
                "Nenhum veículo cadastrado. Vá em Veículos para começar a usar o sistema."
            )
            self.dashboard_content.hide()
            return

        self.empty_state.clear()
        self.dashboard_content.show()

        vid = self.filter_bar.selected_vehicle_id()
        data = get_dashboard_data(vid)

        self.stat_cards["km_atual"].set_value(format_km(data["km_atual"]))
        km_mes = data["km_mes"]
        self.stat_cards["km_mes"].set_value(format_km(km_mes) if km_mes > 0 else "-")
        self.stat_cards["consumo_medio"].set_value(format_consumption(data["consumo_medio"]))
        self.stat_cards["consumo_maximo"].set_value(format_consumption(data["consumo_maximo"]))
        self.stat_cards["consumo_minimo"].set_value(format_consumption(data["consumo_minimo"]))
        self.stat_cards["autonomia"].set_value(format_autonomia(data["autonomia"]))
        self.stat_cards["gasto_mensal"].set_value(format_currency(data["gasto_mensal"]))
        self.stat_cards["gasto_anual"].set_value(format_currency(data["gasto_anual"]))
        self.stat_cards["total_investido"].set_value(format_currency(data["total_investido"]))
        custo = data["custo_km"]
        self.stat_cards["custo_km"].set_value(format_custo_km(custo))

        rev = data["proxima_revisao"]
        if rev:
            self.stat_cards["proxima_revisao"].set_value(
                format_km(rev["proxima_revisao_km"])
            )
        else:
            self.stat_cards["proxima_revisao"].set_value("Sem revisão")

        doc = data["proximo_documento"]
        if doc:
            self.stat_cards["proximo_documento"].set_value(
                f"{doc['tipo']} — {format_document_countdown(doc['dias_restantes'])}"
            )
        else:
            self.stat_cards["proximo_documento"].set_value("Nenhum")

        alerts = data["alertas_documentos"]
        if alerts:
            lines = []
            for alert in alerts[:5]:
                countdown = format_document_countdown(alert["dias_restantes"])
                lines.append(f"⚠ {alert['tipo']} ({alert['placa']}) — {countdown}")
            self.alert_label.setText("\n".join(lines))
            self.btn_view_documents.show()
        else:
            self.alert_label.clear()
            self.btn_view_documents.hide()

        c1 = get_monthly_consumption_chart(vid)
        theme = self._current_theme()
        for chart in (
            self.chart_consumo,
            self.chart_km,
            self.chart_gastos,
            self.chart_distribuicao,
            self.chart_manutencao,
        ):
            chart.set_theme(theme)

        self.chart_consumo.update_chart(c1["labels"], c1["values"])
        c2 = get_odometer_evolution(vid)
        chart_labels = [format_date(label) for label in c2["labels"]]
        self.chart_km.update_chart(chart_labels, c2["values"], "#34a853")
        c3 = get_monthly_spending_chart(vid)
        self.chart_gastos.update_chart(c3["labels"], c3["values"], "#ea4335")
        c4 = get_cost_distribution(vid)
        self.chart_distribuicao.update_chart(c4["labels"], c4["values"])
        c5 = get_maintenance_history_chart(vid)
        self.chart_manutencao.update_chart(c5["labels"], c5["values"], "#fbbc04")

    def _current_theme(self) -> str:
        from motocontrol.database.repositories import SettingsRepository

        return SettingsRepository.get("theme", "dark")
