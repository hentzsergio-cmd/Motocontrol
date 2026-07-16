# MOTOCONTROL PRO v1.0

Sistema de Gestão de Frota Particular para controle completo de motocicletas e veículos particulares.

## Requisitos

- Python 3.12+ (testado com 3.13)
- Windows 10/11

## Instalação

```powershell
cd C:\Users\sergi\Projects\motocontrol-pro
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> Se a instalação do PySide6 falhar por caminho longo no Windows, habilite [Long Paths](https://pip.pypa.io/warnings/enable-long-paths) ou use um venv em pasta curta (ex.: `C:\dev\motocontrol-pro`).

## Executar

```powershell
python main.py
```

## Módulos

| Módulo | Funcionalidades |
|--------|-----------------|
| **Dashboard** | KM atual, consumo, gastos, autonomia, revisão, alertas e 5 gráficos |
| **Veículos** | Cadastro multi-veículo (marca, modelo, ano, placa, RENAVAM, compra) |
| **Abastecimentos** | KM/L, média geral, custo por KM |
| **Manutenções** | 8 categorias (óleo, filtros, pneus, revisão, etc.) |
| **Documentação** | IPVA, licenciamento, seguro, CRLV, garantias + alertas (60/30/15/7 dias) |
| **Financeiro** | Gasto mensal/anual, custo/KM, total investido, categorias |
| **Relatórios** | PDF, XLSX e CSV (histórico, financeiro, consumo, manutenções) |
| **Configurações** | Dark/Light mode, backup diário/semanal/mensal e manual |

## Estrutura

```
motocontrol-pro/
├── main.py                 # Ponto de entrada
├── motocontrol/
│   ├── app.py              # Bootstrap da aplicação
│   ├── config.py           # Constantes e caminhos
│   ├── database/           # SQLite + repositórios
│   ├── services/           # Cálculos, backup, relatórios
│   └── ui/                 # Interface PySide6
├── data/                   # Banco SQLite local
└── backups/                # Backups automáticos e manuais
```

## Gerar executável

```powershell
pyinstaller --noconfirm --windowed --name MOTOCONTROL_PRO main.py
```

## Versão 2.0 (planejado)

OCR de notas, leitura de hodômetro por foto, apps mobile, nuvem, IA preventiva e Power BI.
