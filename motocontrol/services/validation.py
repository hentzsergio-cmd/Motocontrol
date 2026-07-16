import re

PLACA_PATTERN = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")


def normalize_placa(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value.strip()).upper()


def validate_placa(value: str) -> tuple[bool, str]:
    placa = normalize_placa(value)
    if len(placa) != 7:
        return False, "A placa deve ter 7 caracteres (ex.: ABC1D23)."
    if not PLACA_PATTERN.match(placa):
        return False, "Placa inválida. Use o padrão Mercosul (ABC1D23) ou antigo (ABC1234)."
    return True, placa
