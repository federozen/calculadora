"""Estado de Copa Argentina recuperado de la foto documentada en este paquete.

No representa una actualización a hoy: conserva la referencia del 27/09/2026.
"""
from lpf_clubs import canon_club

ALIVE = (
    "Banfield", "Atlético Tucumán", "Boca Juniors",
    "Platense", "Estudiantes de La Plata",
)
UPDATED = "27/09/2026 · foto incluida en el paquete; pendiente Platense-Estudiantes LP"
SOURCE = "Foto documentada en README y CHANGELOG del paquete (27/09/2026)"
SEMIFINALS = (
    ("Boca Juniors", "Banfield"),
    ("Atlético Tucumán", "Ganador de Platense-Estudiantes de La Plata"),
)


def normalize_alive(teams):
    """Canonicaliza y excluye clubes ya eliminados en la foto incluida."""
    result = []
    for raw in teams or ():
        team = canon_club(raw)
        if team in ALIVE and team not in result:
            result.append(team)
    return result


def sync_copa_state(state):
    """Inicializa el estado sin reemplazar una edición o actualización existente."""
    if "LPF_COPA_ARG_VIVOS" not in state:
        state["LPF_COPA_ARG_VIVOS"] = list(ALIVE)
    if "LPF_COPA_ARG_UPDATED" not in state:
        state["LPF_COPA_ARG_UPDATED"] = UPDATED
    if "LPF_COPA_ARG_SOURCE" not in state:
        state["LPF_COPA_ARG_SOURCE"] = SOURCE
    if "lpf_copa_arg_alive_txt" not in state:
        state["lpf_copa_arg_alive_txt"] = "\n".join(state["LPF_COPA_ARG_VIVOS"])
