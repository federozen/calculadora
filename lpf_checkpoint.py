"""Foto inmutable al cierre de F10; los marcadores desde F11 son incrementales.

Fuente: TyC, nota de F10 del 21/09/2026, contrastada con FutbolArgentino.
La tabla de la nota aún omitía Lanús–Estudiantes (2–1) y Barracas–IR (0–1):
se incorporan esos dos resultados explícitos para cerrar los 10 PJ.
No se reconstruyen ni inventan marcadores históricos.
"""
from __future__ import annotations

from copy import deepcopy

from lpf_clubs import canon_club
from lpf_data_2026 import LPF_FIXTURE

LPF_RUNTIME_API = 21
CHECKPOINT_ROUND = 10
CHECKPOINT_SOURCE = "https://www.tycsports.com/liga-profesional-de-futbol/fecha-10-del-clausura-2026-resultados-y-partidos-de-la-liga-profesional-argentina-id761584.html"
CHECKPOINT_UPDATED_AT = "2026-09-22T02:18:00+00:00"

# equipo, puntos, goles a favor, goles en contra
_ROWS = {
    "A": [
        ("Instituto", 22, 13, 7), ("Vélez", 20, 15, 9),
        ("Defensa", 18, 13, 11), ("Gimnasia (M)", 17, 14, 9),
        ("Boca", 17, 14, 11), ("Independiente", 17, 10, 8),
        ("Lanús", 16, 13, 9), ("Newell's", 16, 11, 8),
        ("Unión", 13, 17, 16), ("San Lorenzo", 11, 4, 8),
        ("Estudiantes", 10, 10, 11), ("Riestra", 10, 8, 10),
        ("Platense", 9, 9, 15), ("Talleres", 8, 11, 17),
        ("Central Córdoba", 8, 7, 13),
    ],
    "B": [
        ("Argentinos", 18, 13, 9), ("Rosario Central", 18, 11, 8),
        ("Gimnasia", 17, 15, 15), ("Independiente Rivadavia", 17, 14, 13),
        ("Belgrano", 16, 11, 7), ("Huracán", 16, 10, 8),
        ("Sarmiento", 16, 17, 16), ("River", 13, 13, 12),
        ("Atlético Tucumán", 13, 7, 6), ("Tigre", 12, 9, 9),
        ("Barracas Central", 12, 5, 7), ("Banfield", 9, 11, 16),
        ("Aldosivi", 8, 12, 16), ("Racing", 8, 11, 16),
        ("Estudiantes (Río Cuarto)", 6, 5, 13),
    ],
}


def checkpoint_zones():
    return {
        label: {
            canon_club(team): {"pj": 10, "pts": pts, "gf": gf, "ga": ga,
                               "dg": gf - ga}
            for team, pts, gf, ga in rows
        } for label, rows in _ROWS.items()
    }


def project_checkpoint(played, fixture=LPF_FIXTURE):
    """Recalcula desde la misma base: repetir una actualización no suma dos veces."""
    official = {(g["l"], g["v"]): int(g["f"]) for g in LPF_FIXTURE}
    supplied = {(g["l"], g["v"]): int(g["f"]) for g in fixture}
    if supplied != official:
        raise ValueError("El corte F10 sólo se aplica al fixture LPF Clausura 2026.")
    zones = checkpoint_zones()
    table = {team: row for base in zones.values() for team, row in base.items()}
    known = {}
    for home, away, gh, ga in played or []:
        pair = (home, away)
        if pair not in official or int(gh) < 0 or int(ga) < 0:
            raise ValueError(f"Resultado incompatible con el corte F10: {home}–{away}.")
        if official[pair] <= CHECKPOINT_ROUND:
            continue
        score = (int(gh), int(ga))
        if pair in known and known[pair] != score:
            raise ValueError(f"Marcadores contradictorios: {home}–{away}.")
        known[pair] = score
    for (home, away), (gh, ga) in known.items():
        for team, gf, gc in ((home, gh, ga), (away, ga, gh)):
            row = table[team]
            row["pj"] += 1
            row["pts"] += 3 if gf > gc else 1 if gf == gc else 0
            row["gf"] += gf
            row["ga"] += gc
            row["dg"] = row["gf"] - row["ga"]
    # source_pos de la foto anterior no debe decidir empates tras una actualización.
    return deepcopy(zones)


def checkpoint_matches(zones, played, fixture):
    """Sólo habilita el corte si TODOS los acumulados coinciden exactamente."""
    try:
        projected = project_checkpoint(played, fixture)
        if set(zones) != set(projected):
            return False
        for label, base in projected.items():
            if set(zones[label]) != set(base):
                return False
            for team, row in base.items():
                if any(int(zones[label][team].get(k, 0)) != row[k]
                       for k in ("pj", "pts", "gf", "ga", "dg")):
                    return False
        return True
    except (ValueError, TypeError, KeyError):
        return False


# 150 marcadores explícitos de TyC; acumulados verificados contra _ROWS.
_FIXED_RESULTS = (
    ('Atlético Tucumán', 'Independiente Rivadavia', 0, 0),
    ('Belgrano', 'Rosario Central', 2, 1),
    ('Defensa y Justicia', 'Aldosivi', 1, 1),
    ('Deportivo Riestra', 'Boca Juniors', 3, 0),
    ('Estudiantes de La Plata', 'Independiente', 0, 2),
    ('Estudiantes de Río Cuarto', 'Tigre', 1, 0),
    ('Gimnasia de Mendoza', 'Central Córdoba', 1, 0),
    ('Huracán', 'Banfield', 1, 0),
    ('Lanús', 'San Lorenzo', 1, 0),
    ("Newell's Old Boys", 'Talleres', 1, 0),
    ('Platense', 'Unión', 2, 2),
    ('Racing', 'Gimnasia La Plata', 2, 1),
    ('River Plate', 'Barracas Central', 0, 1),
    ('Sarmiento', 'Argentinos Juniors', 2, 3),
    ('Vélez Sarsfield', 'Instituto', 1, 0),
    ('Argentinos Juniors', 'Estudiantes de Río Cuarto', 3, 0),
    ('Banfield', 'Sarmiento', 3, 2),
    ('Barracas Central', 'Aldosivi', 1, 0),
    ('Boca Juniors', 'Estudiantes de La Plata', 1, 0),
    ('Central Córdoba', 'Atlético Tucumán', 0, 2),
    ('Defensa y Justicia', 'Deportivo Riestra', 2, 1),
    ('Gimnasia La Plata', 'River Plate', 1, 0),
    ('Independiente', "Newell's Old Boys", 1, 0),
    ('Independiente Rivadavia', 'Huracán', 2, 1),
    ('Instituto', 'Platense', 2, 1),
    ('Rosario Central', 'Racing', 0, 0),
    ('San Lorenzo', 'Gimnasia de Mendoza', 1, 0),
    ('Talleres', 'Vélez Sarsfield', 1, 3),
    ('Tigre', 'Belgrano', 0, 0),
    ('Unión', 'Lanús', 2, 1),
    ('Aldosivi', 'Gimnasia La Plata', 1, 2),
    ('Belgrano', 'Argentinos Juniors', 0, 1),
    ('Central Córdoba', 'San Lorenzo', 1, 0),
    ('Deportivo Riestra', 'Barracas Central', 0, 1),
    ('Estudiantes de La Plata', 'Defensa y Justicia', 3, 0),
    ('Estudiantes de Río Cuarto', 'Banfield', 0, 0),
    ('Gimnasia de Mendoza', 'Unión', 2, 0),
    ('Huracán', 'Atlético Tucumán', 0, 0),
    ('Lanús', 'Instituto', 0, 1),
    ("Newell's Old Boys", 'Boca Juniors', 2, 2),
    ('Platense', 'Talleres', 0, 4),
    ('Racing', 'Tigre', 1, 3),
    ('River Plate', 'Rosario Central', 0, 1),
    ('Sarmiento', 'Independiente Rivadavia', 2, 1),
    ('Vélez Sarsfield', 'Independiente', 1, 0),
    ('Argentinos Juniors', 'Racing', 2, 1),
    ('Atlético Tucumán', 'Sarmiento', 1, 2),
    ('Banfield', 'Belgrano', 0, 2),
    ('Boca Juniors', 'Vélez Sarsfield', 1, 1),
    ('Defensa y Justicia', "Newell's Old Boys", 2, 1),
    ('Deportivo Riestra', 'Estudiantes de La Plata', 2, 0),
    ('Gimnasia La Plata', 'Barracas Central', 2, 0),
    ('Independiente', 'Platense', 0, 1),
    ('Independiente Rivadavia', 'Estudiantes de Río Cuarto', 2, 1),
    ('Instituto', 'Gimnasia de Mendoza', 1, 0),
    ('Rosario Central', 'Aldosivi', 2, 1),
    ('San Lorenzo', 'Huracán', 0, 2),
    ('Talleres', 'Lanús', 0, 3),
    ('Tigre', 'River Plate', 1, 0),
    ('Unión', 'Central Córdoba', 1, 2),
    ('Aldosivi', 'Tigre', 0, 0),
    ('Barracas Central', 'Rosario Central', 0, 1),
    ('Belgrano', 'Independiente Rivadavia', 2, 0),
    ('Central Córdoba', 'Instituto', 0, 1),
    ('Estudiantes de La Plata', 'Gimnasia La Plata', 4, 0),
    ('Estudiantes de Río Cuarto', 'Atlético Tucumán', 0, 1),
    ('Gimnasia de Mendoza', 'Talleres', 3, 1),
    ('Lanús', 'Independiente', 1, 3),
    ("Newell's Old Boys", 'Deportivo Riestra', 2, 0),
    ('Platense', 'Boca Juniors', 1, 1),
    ('Racing', 'Banfield', 0, 1),
    ('River Plate', 'Argentinos Juniors', 2, 0),
    ('San Lorenzo', 'Unión', 1, 0),
    ('Sarmiento', 'Huracán', 2, 0),
    ('Vélez Sarsfield', 'Defensa y Justicia', 1, 1),
    ('Aldosivi', 'Unión', 1, 3),
    ('Atlético Tucumán', 'Instituto', 0, 0),
    ('Barracas Central', 'Platense', 1, 2),
    ('Belgrano', 'Defensa y Justicia', 1, 2),
    ('Estudiantes de Río Cuarto', 'San Lorenzo', 0, 0),
    ('Gimnasia La Plata', 'Gimnasia de Mendoza', 2, 3),
    ('Huracán', 'Deportivo Riestra', 0, 0),
    ('Independiente', 'Independiente Rivadavia', 0, 0),
    ('Lanús', 'Argentinos Juniors', 1, 1),
    ("Newell's Old Boys", 'Banfield', 2, 1),
    ('Racing', 'Boca Juniors', 1, 1),
    ('River Plate', 'Vélez Sarsfield', 2, 2),
    ('Sarmiento', 'Estudiantes de La Plata', 2, 0),
    ('Talleres', 'Rosario Central', 2, 2),
    ('Tigre', 'Central Córdoba', 2, 1),
    ('Argentinos Juniors', 'Aldosivi', 2, 1),
    ('Atlético Tucumán', 'Belgrano', 0, 0),
    ('Banfield', 'River Plate', 2, 3),
    ('Boca Juniors', 'Lanús', 1, 0),
    ('Defensa y Justicia', 'Platense', 1, 0),
    ('Deportivo Riestra', 'Vélez Sarsfield', 1, 1),
    ('Estudiantes de La Plata', "Newell's Old Boys", 0, 0),
    ('Huracán', 'Estudiantes de Río Cuarto', 1, 1),
    ('Independiente', 'Gimnasia de Mendoza', 0, 3),
    ('Independiente Rivadavia', 'Racing', 3, 1),
    ('Instituto', 'San Lorenzo', 1, 0),
    ('Rosario Central', 'Gimnasia La Plata', 1, 2),
    ('Talleres', 'Central Córdoba', 0, 0),
    ('Tigre', 'Barracas Central', 0, 0),
    ('Unión', 'Sarmiento', 4, 1),
    ('Aldosivi', 'Banfield', 3, 1),
    ('Barracas Central', 'Argentinos Juniors', 0, 0),
    ('Belgrano', 'Huracán', 1, 1),
    ('Central Córdoba', 'Independiente', 0, 1),
    ('Estudiantes de Río Cuarto', 'Sarmiento', 0, 2),
    ('Gimnasia La Plata', 'Tigre', 2, 1),
    ('Gimnasia de Mendoza', 'Boca Juniors', 2, 2),
    ('Lanús', 'Defensa y Justicia', 1, 0),
    ('Platense', 'Deportivo Riestra', 1, 1),
    ('Racing', 'Atlético Tucumán', 1, 2),
    ('River Plate', 'Independiente Rivadavia', 3, 1),
    ('Rosario Central', "Newell's Old Boys", 1, 1),
    ('San Lorenzo', 'Talleres', 1, 0),
    ('Unión', 'Instituto', 3, 2),
    ('Vélez Sarsfield', 'Estudiantes de La Plata', 1, 0),
    ('Argentinos Juniors', 'Gimnasia La Plata', 1, 1),
    ('Atlético Tucumán', 'River Plate', 1, 2),
    ('Banfield', 'Barracas Central', 1, 1),
    ('Boca Juniors', 'Central Córdoba', 3, 1),
    ('Defensa y Justicia', 'Gimnasia de Mendoza', 2, 0),
    ('Deportivo Riestra', 'Lanús', 0, 3),
    ('Estudiantes de La Plata', 'Platense', 2, 1),
    ('Huracán', 'Racing', 2, 1),
    ('Independiente', 'San Lorenzo', 1, 1),
    ('Independiente Rivadavia', 'Aldosivi', 4, 3),
    ('Instituto', 'Estudiantes de Río Cuarto', 2, 1),
    ("Newell's Old Boys", 'Vélez Sarsfield', 1, 1),
    ('Sarmiento', 'Belgrano', 1, 1),
    ('Talleres', 'Unión', 2, 1),
    ('Tigre', 'Rosario Central', 0, 1),
    ('Aldosivi', 'Atlético Tucumán', 1, 0),
    ('Barracas Central', 'Independiente Rivadavia', 0, 1),
    ('Belgrano', 'Estudiantes de Río Cuarto', 2, 1),
    ('Central Córdoba', 'Defensa y Justicia', 2, 2),
    ('Gimnasia La Plata', 'Banfield', 2, 2),
    ('Gimnasia de Mendoza', 'Deportivo Riestra', 0, 0),
    ('Instituto', 'Talleres', 3, 1),
    ('Lanús', 'Estudiantes de La Plata', 2, 1),
    ('Platense', "Newell's Old Boys", 0, 1),
    ('Racing', 'Sarmiento', 3, 1),
    ('River Plate', 'Huracán', 1, 2),
    ('Rosario Central', 'Argentinos Juniors', 1, 0),
    ('San Lorenzo', 'Boca Juniors', 0, 2),
    ('Unión', 'Independiente', 1, 2),
    ('Vélez Sarsfield', 'Tigre', 3, 2),
)


def checkpoint_results():
    return list(_FIXED_RESULTS)


def cached_results(path=None):
    """El cache preserva los resultados nuevos también después de un reinicio."""
    import json
    from pathlib import Path
    target = Path(path) if path else Path(__file__).parent / "data" / "lpf_since_round11.json"
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        if payload.get("competition") != "LPF Clausura 2026":
            return []
        rows = [tuple(r) for r in payload["played"]]
        project_checkpoint(rows)
        rounds = {(g["l"], g["v"]): int(g["f"]) for g in LPF_FIXTURE}
        return [r for r in rows if rounds[(r[0], r[1])] > CHECKPOINT_ROUND]
    except (OSError, ValueError, TypeError, KeyError):
        return []


def save_recent_results(played, path=None, *, source_urls=()):
    import json
    from pathlib import Path
    from datetime import datetime, timezone
    project_checkpoint(played)
    rounds = {(g["l"], g["v"]): int(g["f"]) for g in LPF_FIXTURE}
    recent = [r for r in played if rounds[(r[0], r[1])] > CHECKPOINT_ROUND]
    target = Path(path) if path else Path(__file__).parent / "data" / "lpf_since_round11.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps({"competition": "LPF Clausura 2026",
                              "updated_at": datetime.now(timezone.utc).isoformat(),
                              "source_urls": list(source_urls),
                              "played": recent}, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(target)
