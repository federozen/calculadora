"""
⚽ Calculadora de escenarios — Mundial 2026
Convertido de Jupyter Notebook a Streamlit
"""

import streamlit as st
from itertools import product, combinations
import pandas as pd
import numpy as np
import re
import requests

# ─── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="⚽ Calculadora Mundial 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 2rem 2rem 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    border-left: 4px solid #e94560;
}
.main-header h1 { color: white; font-size: 2rem; font-weight: 700; margin: 0; }
.main-header p { color: #a0aec0; margin: 0.3rem 0 0; font-size: 0.95rem; }

.section-card {
    background: #f8f9fa;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}

.estado-verde { color: #22c55e; font-weight: 600; }
.estado-rojo  { color: #ef4444; font-weight: 600; }
.estado-amarillo { color: #f59e0b; font-weight: 600; }
.estado-azul  { color: #3b82f6; font-weight: 600; }

div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── MOTOR ─────────────────────────────────────────────────────────────────────

PRESETS = {
    "Olímpico — mano a mano primero (FIFA, Euro, La Liga, Serie A)": ["h2h_pts","h2h_dg","h2h_gf","dg","gf"],
    "Diferencia de gol primero (Premier, Bundesliga, Champions fase liga)": ["dg","gf"],
    "Solo puntos (sin desempate fino)": [],
}

if "CRITERIOS" not in st.session_state:
    st.session_state.CRITERIOS = ["h2h_pts","h2h_dg","h2h_gf","dg","gf"]
if "ESTADO" not in st.session_state:
    st.session_state.ESTADO = {}

def fixture_completo(equipos): return list(combinations(equipos, 2))

def _stats(equipos, partidos):
    st_d = {e: {"pts": 0, "gf": 0, "ga": 0, "pj": 0} for e in equipos}
    for l, v, gl, gv in partidos:
        st_d[l]["gf"] += gl; st_d[l]["ga"] += gv; st_d[l]["pj"] += 1
        st_d[v]["gf"] += gv; st_d[v]["ga"] += gl; st_d[v]["pj"] += 1
        if gl > gv: st_d[l]["pts"] += 3
        elif gl < gv: st_d[v]["pts"] += 3
        else: st_d[l]["pts"] += 1; st_d[v]["pts"] += 1
    for e in st_d: st_d[e]["dg"] = st_d[e]["gf"] - st_d[e]["ga"]
    return st_d

def _stats_entre(teams, partidos):
    ts = set(teams)
    st_d = {e: {"pts": 0, "gf": 0, "ga": 0} for e in teams}
    for l, v, gl, gv in partidos:
        if l in ts and v in ts:
            st_d[l]["gf"] += gl; st_d[l]["ga"] += gv
            st_d[v]["gf"] += gv; st_d[v]["ga"] += gl
            if gl > gv: st_d[l]["pts"] += 3
            elif gl < gv: st_d[v]["pts"] += 3
            else: st_d[l]["pts"] += 1; st_d[v]["pts"] += 1
    for e in st_d: st_d[e]["dg"] = st_d[e]["gf"] - st_d[e]["ga"]
    return st_d

def _resolver(teams, partidos, overall, fair_play, ranking):
    criterios = st.session_state.CRITERIOS
    if len(teams) <= 1: return list(teams)
    h = _stats_entre(teams, partidos) if any(c.startswith("h2h") for c in criterios) else None
    def val(c):
        if c == "h2h_pts": return {e: h[e]["pts"] for e in teams}
        if c == "h2h_dg":  return {e: h[e]["dg"] for e in teams}
        if c == "h2h_gf":  return {e: h[e]["gf"] for e in teams}
        if c == "dg":      return {e: overall[e]["dg"] for e in teams}
        if c == "gf":      return {e: overall[e]["gf"] for e in teams}
        if c == "fair_play" and fair_play is not None: return {e: fair_play.get(e, 0) for e in teams}
        if c == "ranking" and ranking is not None: return {e: -ranking.get(e, 9999) for e in teams}
        return None
    for c in criterios:
        vals = val(c)
        if vals is None: continue
        if len(set(vals.values())) > 1:
            out = []
            for v in sorted(set(vals.values()), reverse=True):
                out += _resolver([e for e in teams if vals[e] == v], partidos, overall, fair_play, ranking)
            return out
    return sorted(teams)

def _orden(equipos, partidos, fair_play=None, ranking=None):
    overall = _stats(equipos, partidos); porpts = {}
    for e in equipos: porpts.setdefault(overall[e]["pts"], []).append(e)
    orden = []
    for pts in sorted(porpts, reverse=True):
        orden += _resolver(porpts[pts], partidos, overall, fair_play, ranking)
    return orden, overall

def posiciones(equipos, partidos, fair_play=None, ranking=None):
    orden, _ = _orden(equipos, partidos, fair_play, ranking)
    return {e: i for i, e in enumerate(orden, 1)}

def tabla(equipos, partidos, fair_play=None, ranking=None):
    orden, ov = _orden(equipos, partidos, fair_play, ranking)
    return pd.DataFrame([{"Pos": i, "Equipo": e, "PJ": ov[e]["pj"], "PTS": ov[e]["pts"],
                          "GF": ov[e]["gf"], "GC": ov[e]["ga"], "DG": ov[e]["dg"]}
                         for i, e in enumerate(orden, 1)])

def simular(equipos, jugados, pendientes, resultados, fair_play=None, ranking=None):
    part = list(jugados) + [(l, v, gl, gv) for (l, v), (gl, gv) in zip(pendientes, resultados)]
    return tabla(equipos, part, fair_play, ranking)

def texto_resultados(pend, res):
    return " | ".join(f"{l} {gl}-{gv} {v}" for (l, v), (gl, gv) in zip(pend, res))

def elegir_max_goles(n_pend, tope=300000):
    for mg in (5, 4, 3, 2, 1):
        if (mg + 1) ** (2 * n_pend) <= tope: return mg
    return 1

def todos_los_escenarios(equipos, jugados, pendientes, max_goles=None, fair_play=None, ranking=None):
    if max_goles is None: max_goles = elegir_max_goles(len(pendientes))
    posib = list(product(range(max_goles + 1), repeat=2)); filas = []
    for res in product(posib, repeat=len(pendientes)):
        t = simular(equipos, jugados, pendientes, res, fair_play, ranking)
        fila = {"Resultados": texto_resultados(pendientes, res)}
        for i, ((l, v), (gl, gv)) in enumerate(zip(pendientes, res), 1):
            fila[f"P{i}_local"] = l; fila[f"P{i}_vis"] = v; fila[f"P{i}_gl"] = gl; fila[f"P{i}_gv"] = gv
        for _, r in t.iterrows():
            e = r["Equipo"]; fila[f"Pos {e}"] = r["Pos"]; fila[f"PTS {e}"] = r["PTS"]
            fila[f"DG {e}"] = r["DG"]; fila[f"GF {e}"] = r["GF"]
        filas.append(fila)
    return pd.DataFrame(filas)

# ─── ANÁLISIS ──────────────────────────────────────────────────────────────────

def _pd_de(equipo, pend): return [(i, l, v) for i, (l, v) in enumerate(pend, 1) if equipo in (l, v)]

def _res_propio(row, equipo, pend):
    et = []
    for i, l, v in _pd_de(equipo, pend):
        gl, gv = row[f"P{i}_gl"], row[f"P{i}_gv"]
        gf, gc = (gl, gv) if l == equipo else (gv, gl); riv = v if l == equipo else l
        et.append(f"le gana a {riv}" if gf > gc else (f"pierde con {riv}" if gf < gc else f"empata con {riv}"))
    return " y ".join(et)

def _res_otros(row, equipo, pend):
    et = []; mios = {i for i, _, _ in _pd_de(equipo, pend)}
    for i, (l, v) in enumerate(pend, 1):
        if i in mios: continue
        gl, gv = row[f"P{i}_gl"], row[f"P{i}_gv"]
        et.append(f"gana {l}" if gl > gv else (f"gana {v}" if gl < gv else f"empatan {l} y {v}"))
    return " y ".join(et) if et else "(no hay otros partidos)"

def _combo(row, pend):
    parts = []
    for i, (l, v) in enumerate(pend, 1):
        gl, gv = row[f"P{i}_gl"], row[f"P{i}_gv"]
        parts.append(f"gana {l}" if gl > gv else (f"gana {v}" if gl < gv else f"empatan {l} y {v}"))
    return " · ".join(parts)

def situacion(equipo, esc, directo=2):
    pos = esc[f"Pos {equipo}"]
    return {"mejor": int(pos.min()), "peor": int(pos.max()), "total": len(esc),
            "n1": int((pos == 1).sum()), "ndir": int((pos <= directo).sum()), "ntop3": int((pos <= 3).sum()),
            "ya_1": bool((pos == 1).all()), "ya_directo": bool((pos <= directo).all()),
            "asegura_top3": bool((pos <= 3).all()), "puede_1": bool((pos == 1).any()),
            "puede_directo": bool((pos <= directo).any()), "puede_top3": bool((pos <= 3).any()),
            "eliminado": bool((pos > 3).all())}

def que_necesita_texto(equipo, esc, pend, objetivo="directo", directo=2, n=2):
    pos = esc[f"Pos {equipo}"]
    T = sum(1 for c in esc.columns if c.startswith("Pos "))
    if objetivo in ("primero", "campeon"):
        ok = (pos == 1); verbo = "es campeón"
    elif objetivo == "top3":
        ok = (pos <= 3); verbo = "queda 3º o mejor"
    elif objetivo == "top":
        ok = (pos <= n); verbo = f"entra al top {n}"
    elif objetivo == "exacto":
        ok = (pos == n); verbo = f"queda {n}º"
    elif objetivo == "descenso":
        corte = T - n; ok = (pos <= corte); verbo = "se salva"
    else:
        ok = (pos <= directo); verbo = "clasifica"
    df = esc.copy()
    df["_p"] = df.apply(lambda r: _res_propio(r, equipo, pend), axis=1)
    df["_o"] = df.apply(lambda r: _res_otros(r, equipo, pend), axis=1)
    df["_ok"] = ok.values
    lineas = []
    for prop, g in sorted(df.groupby("_p"), key=lambda kv: -kv[1]["_ok"].mean()):
        m, k = len(g), int(g["_ok"].sum())
        cab = "✅ SEGURO" if k == m else ("❌ IMPOSIBLE" if k == 0 else "⚠️ DEPENDE")
        lineas.append(f"**• Si {equipo} {prop}:** {cab}")
        if 0 < k < m:
            for otros, g2 in sorted(g.groupby("_o"), key=lambda kv: -kv[1]["_ok"].mean()):
                n2, k2 = len(g2), int(g2["_ok"].sum())
                e = f"→ {verbo} ✅" if k2 == n2 else (f"→ no {verbo} ❌" if k2 == 0 else "→ depende de la dif. de gol ⚠️")
                lineas.append(f"&nbsp;&nbsp;&nbsp;&nbsp;· y {otros}: {e}")
    return "\n\n".join(lineas)

def panorama(equipos, jugados, esc, directo=2):
    filas = []
    for e in equipos:
        s = situacion(e, esc, directo)
        est = ("🟢 Clasificado directo" if s["ya_directo"] else "🔴 Eliminado" if s["eliminado"]
               else "🟡 En disputa" if s["puede_directo"] else "🔵 Sólo como mejor 3º")
        filas.append({"Equipo": e, "Estado": est, "Mejor": s["mejor"], "Peor": s["peor"],
                      "Puede 1º": "sí" if s["puede_1"] else "no",
                      "Directo en": f"{s['ndir']}/{s['total']}"})
    orden = {r["Equipo"]: r["Pos"] for _, r in tabla(equipos, jugados).iterrows()}
    return pd.DataFrame(filas).sort_values("Equipo", key=lambda c: c.map(orden)).reset_index(drop=True)

def _desc_obj(o):
    return {"exacto": f"exactamente {o[1]}º", "al_menos": f"{o[1]}º o mejor",
            "como_mucho": f"{o[1]}º o peor", "entre": f"entre {o[1]}º y {o[-1]}º"}[o[0]]

def _ok_pos(pos, o):
    if o[0] == "exacto": return pos == o[1]
    if o[0] == "al_menos": return pos <= o[1]
    if o[0] == "como_mucho": return pos >= o[1]
    return (pos >= o[1]) & (pos <= o[2])

def resultados_para_puesto_texto(equipo, esc, pend, objetivo):
    pos = esc[f"Pos {equipo}"]; ok = _ok_pos(pos, objetivo); desc = _desc_obj(objetivo)
    n, tot = int(ok.sum()), len(esc)
    if n == 0:
        alc = ", ".join(f"{int(p)}º" for p in sorted(pos.unique()))
        return f"❌ **IMPOSIBLE**: {equipo} no puede terminar {desc}.\n\nPuestos alcanzables: {alc}."
    if n == tot:
        return f"✅ {equipo} termina {desc} **pase lo que pase**."
    df = esc.copy(); df["_c"] = df.apply(lambda r: _combo(r, pend), axis=1); df["_ok"] = ok.values
    siempre, aveces = [], []
    for c, g in df.groupby("_c"):
        k, m = int(g["_ok"].sum()), len(g)
        if k == m: siempre.append(c)
        elif k > 0: aveces.append((c, k, m))
    lineas = []
    if siempre:
        lineas.append("**Lo logra SIEMPRE con:**")
        for c in siempre: lineas.append(f"✅ {c}")
    if aveces:
        lineas.append("\n**Lo logra SOLO si la dif. de gol acompaña:**")
        for c, k, m in sorted(aveces, key=lambda x: -x[1]/x[2]):
            lineas.append(f"⚠️ {c} &nbsp;({k}/{m} marcadores)")
    return "\n\n".join(lineas)

def probabilidades(equipos, jugados, pendientes, n=8000, media=1.3, seed=1):
    rng = np.random.default_rng(seed)
    lam = {e: media for e in equipos}
    cuenta = {e: np.zeros(len(equipos) + 1, dtype=int) for e in equipos}
    base = list(jugados)
    for _ in range(n):
        part = base + [(l, v, int(rng.poisson(lam[l])), int(rng.poisson(lam[v]))) for (l, v) in pendientes]
        for e, p in posiciones(equipos, part).items(): cuenta[e][p] += 1
    rows = [{"Equipo": e, "1º %": round(100 * cuenta[e][1] / n, 1),
             "Top 2 %": round(100 * cuenta[e][1:3].sum() / n, 1),
             "Top 3 %": round(100 * cuenta[e][1:4].sum() / n, 1)} for e in equipos]
    return pd.DataFrame(rows).sort_values("Top 2 %", ascending=False).reset_index(drop=True)

def que_pasa_si(esc, pend, condiciones, equipos):
    mask = pd.Series(True, index=esc.index)
    for i, cond in enumerate(condiciones, 1):
        if not cond: continue
        gl, gv = esc[f"P{i}_gl"], esc[f"P{i}_gv"]
        mask &= (gl > gv) if cond == "L" else (gl == gv) if cond == "E" else (gl < gv)
    sub = esc[mask]
    rows = [{"Equipo": e, "Mejor": int(sub[f"Pos {e}"].min()), "Peor": int(sub[f"Pos {e}"].max()),
             "Directo posible": "sí" if (sub[f"Pos {e}"] <= 2).any() else "no",
             "Directo seguro": "sí" if (sub[f"Pos {e}"] <= 2).all() else "no"} for e in equipos]
    return sub, pd.DataFrame(rows)

def distribucion(equipos, esc):
    d = pd.DataFrame({e: esc[f"Pos {e}"].value_counts() for e in equipos}).fillna(0).astype(int).sort_index()
    d.index.name = "Puesto"; return d

def maximos_minimos(equipos, jugados, pend):
    ov = _stats(equipos, jugados)
    rest = {e: 0 for e in equipos}
    for l, v in pend: rest[l] += 1; rest[v] += 1
    rows = [{"Equipo": e, "PJ": ov[e]["pj"], "PTS": ov[e]["pts"], "Restan": rest[e],
             "PTS máx": ov[e]["pts"] + 3 * rest[e]} for e in equipos]
    return pd.DataFrame(rows).sort_values(["PTS", "PTS máx"], ascending=False).reset_index(drop=True)

def clasificado_eliminado(equipos, jugados, pend, n=1):
    ov = _stats(equipos, jugados)
    rest = {e: 0 for e in equipos}
    for l, v in pend: rest[l] += 1; rest[v] += 1
    pts = {e: ov[e]["pts"] for e in equipos}
    pmax = {e: pts[e] + 3 * rest[e] for e in equipos}
    rows = []
    for e in equipos:
        arriba = sum(1 for x in equipos if x != e and pmax[x] > pts[e])
        inalc  = sum(1 for x in equipos if x != e and pts[x] > pmax[e])
        estado = "🟢 asegurado" if arriba < n else ("🔴 sin chances" if inalc >= n else "🟡 depende")
        rows.append({"Equipo": e, "PTS": pts[e], "PTS máx": pmax[e], f"Top {n}": estado})
    return pd.DataFrame(rows).sort_values("PTS", ascending=False).reset_index(drop=True)

def numero_magico_texto(equipo, equipos, jugados, pend, n=1):
    ov = _stats(equipos, jugados)
    rest = {e: 0 for e in equipos}
    for l, v in pend: rest[l] += 1; rest[v] += 1
    pts = {e: ov[e]["pts"] for e in equipos}
    pmax = {e: pts[e] + 3 * rest[e] for e in equipos}
    otros = sorted((pmax[x] for x in equipos if x != equipo), reverse=True)
    meta = "ser campeón" if n == 1 else f"entrar al top {n}"
    lineas = [f"**{equipo}** — para {meta}:",
              f"Tiene **{pts[equipo]} pts** y le quedan {rest[equipo]} partidos ({3*rest[equipo]} en juego)."]
    if len(otros) < n:
        lineas.append(f"✅ Ya está en el top {n}.")
    else:
        necesita = max(0, (otros[n-1] + 1) - pts[equipo]); tope = 3 * rest[equipo]
        if necesita == 0:
            lineas.append("✅ Ya está asegurado pase lo que pase.")
        elif necesita <= tope:
            lineas.append(f"Necesita sumar **{necesita} pts** más para asegurarlo sin depender de nadie.")
        else:
            lineas.append(f"No puede asegurarlo solo: necesitaría {necesita} y solo hay {tope} en juego → depende de que los rivales pinchen.")
    return "\n\n".join(lineas)

def mejor_resultado_texto(equipo, esc, pend, directo=2):
    df = esc.copy()
    df["_p"] = df.apply(lambda r: _res_propio(r, equipo, pend), axis=1)
    opciones = []
    for prop, g in df.groupby("_p"):
        gp = esc.loc[g.index, f"Pos {equipo}"]
        opciones.append({"r": prop, "peor": int(gp.max()), "mejor": int(gp.min()),
                         "dir": int((gp <= directo).sum()), "n": len(g)})
    opciones.sort(key=lambda o: (o["peor"], o["mejor"], -o["dir"]/o["n"]))
    lineas = []
    for i, o in enumerate(opciones):
        flag = " 👍 lo que más le conviene" if i == 0 else ""
        lineas.append(f"• Si {equipo} **{o['r']}**: termina entre {o['mejor']}º y {o['peor']}º · clasifica directo en {o['dir']}/{o['n']}{flag}")
    return "\n\n".join(lineas)

# ─── PARSER ────────────────────────────────────────────────────────────────────

_MESES = r"(ene|feb|mar|abr|may|jun|jul|ago|sep|set|oct|nov|dic|jan|apr|aug|dec)"
_DIAS  = r"(lun|mar|mié|mie|jue|vie|sáb|sab|dom|mon|tue|wed|thu|fri|sat|sun)"
_RE_SCORE = re.compile(r"^(.+?)\s+(\d{1,2})\s*(?:[-–—xX]\s*(\d{1,2})|:\s*(\d))\s+(.+?)$")
_RE_VS    = re.compile(r"^(.+?)\s+(?:vs?\.?|–|—|-|x)\s+(.+?)$", re.I)

def _limpiar(ln):
    ln = ln.strip()
    pref = [rf"^{_DIAS}\w*\.?,?\s+", r"^\d{{1,2}}[:.]\\d{{2}}\s+",
            r"^\d{1,2}[/\-.]\d{1,2}([/\-.]\d{2,4})?\s+",
            rf"^\d{{1,2}}\s+{_MESES}\w*\.?,?\s+", rf"^{_MESES}\w*\.?\s+\d{{1,2}},?\s+"]
    ch = True
    while ch:
        ch = False
        for p in pref:
            nu = re.sub(p, "", ln, flags=re.I)
            if nu != ln: ln = nu; ch = True
    ln = re.sub(r"\s*\(.*?\)\s*$", "", ln)
    ln = re.sub(r"\s*(FT|Finalizado|Final|Termin\w*|Ver resumen|Resumen)\s*$", "", ln, flags=re.I)
    return ln.strip()

def _norm(t): return re.sub(r"\s+", " ", t).strip(" -–—\t")
def _let(t): return bool(re.search(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]", t))

def parsear_resultados(texto):
    jug, pen, eq = [], [], []
    def add(t):
        if t and t not in eq: eq.append(t)
    for raw in texto.splitlines():
        ln = _limpiar(raw)
        if not ln: continue
        m = _RE_SCORE.match(ln)
        if m:
            loc, vis = _norm(m.group(1)), _norm(m.group(5))
            gl = int(m.group(2)); gv = int(m.group(3) if m.group(3) is not None else m.group(4))
            if _let(loc) and _let(vis): add(loc); add(vis); jug.append((loc, vis, gl, gv)); continue
        m = _RE_VS.match(ln)
        if m:
            loc, vis = _norm(m.group(1)), _norm(m.group(2))
            if _let(loc) and _let(vis) and not re.search(r"\d", loc + vis):
                add(loc); add(vis); pen.append((loc, vis))
    jp = {frozenset((l, v)) for l, v, _, _ in jug}
    pp = {frozenset(p) for p in pen}
    for a, b in combinations(eq, 2):
        fs = frozenset((a, b))
        if fs not in jp and fs not in pp: pen.append((a, b)); pp.add(fs)
    return eq, jug, pen

_RE_HEADER = re.compile(r"^\s*(grupo|group|gpo)\s*[:.]?\s*([A-Za-z0-9]+)\s*$", re.I)

def dividir_grupos(texto):
    g, act, suelto = {}, None, []
    for ln in texto.splitlines():
        m = _RE_HEADER.match(ln.strip())
        if m: act = m.group(2).upper(); g.setdefault(act, [])
        else: (g[act] if act is not None else suelto).append(ln)
    if not g and any(s.strip() for s in suelto): g["Único"] = suelto
    return {k: "\n".join(v) for k, v in g.items()}

# ─── API ───────────────────────────────────────────────────────────────────────

_FIN = {"FINISHED", "AWARDED"}

def _grp(lbl): return re.split(r"[ _]", str(lbl).strip())[-1].upper() if lbl else "?"
def _nom(t): return (t.get("shortName") or t.get("name") or t.get("tla") or "¿?").strip()

def matches_a_texto(matches):
    grupos = {}
    for m in matches:
        if "GROUP" not in str(m.get("stage", "")).upper() and not m.get("group"): continue
        g = _grp(m.get("group")); loc, vis = _nom(m["homeTeam"]), _nom(m["awayTeam"])
        ft = (m.get("score") or {}).get("fullTime") or {}; gl, gv = ft.get("home"), ft.get("away")
        if m.get("status") in _FIN and gl is not None and gv is not None:
            grupos.setdefault(g, []).append(f"{loc} {gl}-{gv} {vis}")
        else:
            grupos.setdefault(g, []).append(f"{loc} vs {vis}")
    out = []
    for g in sorted(grupos): out.append(f"Grupo {g}"); out.extend(grupos[g]); out.append("")
    return "\n".join(out).strip()

def traer_de_api(token, comp="WC"):
    r = requests.get(f"https://api.football-data.org/v4/competitions/{comp}/matches",
                     headers={"X-Auth-Token": token}, timeout=30)
    r.raise_for_status()
    return r.json().get("matches", [])

def listar_competiciones(token):
    r = requests.get("https://api.football-data.org/v4/competitions",
                     headers={"X-Auth-Token": token}, timeout=30)
    r.raise_for_status()
    return [(c.get("code"), c.get("name")) for c in r.json().get("competitions", [])]

# ─── HELPER: cargar estado ─────────────────────────────────────────────────────

def cargar_estado(equipos, jugados, pendientes):
    mg = elegir_max_goles(len(pendientes))
    with st.spinner(f"Calculando {(mg+1)**(2*len(pendientes))} escenarios…"):
        esc = todos_los_escenarios(equipos, jugados, pendientes, mg)
    st.session_state.ESTADO = dict(equipos=equipos, jugados=jugados, pendientes=pendientes, esc=esc, mg=mg)
    return esc

# ═══════════════════════════════════════════════════════════════════════════════
# UI
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="main-header">
  <h1>⚽ Calculadora Mundial 2026</h1>
  <p>Análisis de escenarios, clasificación y desempate FIFA por grupo</p>
</div>
""", unsafe_allow_html=True)

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔧 Configuración")

    # Desempate
    st.subheader("Criterio de desempate")
    preset_sel = st.selectbox("Regla", list(PRESETS.keys()), label_visibility="collapsed")
    if PRESETS[preset_sel] != st.session_state.CRITERIOS:
        st.session_state.CRITERIOS = PRESETS[preset_sel]
        if st.session_state.ESTADO:
            E = st.session_state.ESTADO
            cargar_estado(E["equipos"], E["jugados"], E["pendientes"])
            st.rerun()

    st.divider()

    # Cargar datos
    st.subheader("📥 Cargar datos")
    modo_carga = st.radio("Fuente", ["API football-data.org", "Pegar texto"], label_visibility="collapsed")

    texto_torneo = ""

    if modo_carga == "API football-data.org":
        token = st.text_input("API Key", type="password", placeholder="Tu token de football-data.org")
        comp  = st.text_input("Código torneo", value="WC", help="WC = Mundial, CL = Champions, etc.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌐 Traer datos", use_container_width=True):
                if not token:
                    st.error("Pegá tu API key.")
                else:
                    try:
                        with st.spinner("Trayendo…"):
                            matches = traer_de_api(token, comp)
                        texto_torneo = matches_a_texto(matches)
                        st.session_state["texto_torneo_cache"] = texto_torneo
                        st.success("Datos cargados ✓")
                    except Exception as e:
                        st.error(f"Error: {e}")
        with col2:
            if st.button("Ver torneos", use_container_width=True):
                if token:
                    try:
                        comps = listar_competiciones(token)
                        st.session_state["lista_comps"] = comps
                    except Exception as e:
                        st.error(str(e))
        if "lista_comps" in st.session_state:
            for code, name in st.session_state["lista_comps"]:
                st.caption(f"`{code}` — {name}")
        texto_torneo = st.session_state.get("texto_torneo_cache", "")

    else:
        texto_torneo = st.text_area(
            "Pegá los resultados",
            height=200,
            placeholder="Grupo A\nEspaña 0-0 Cabo Verde\nUruguay 1-1 Arabia Saudita\n...",
        )

    grupos_disponibles = list(dividir_grupos(texto_torneo).keys()) if texto_torneo.strip() else []

    if grupos_disponibles:
        grupo_sel = st.selectbox("📂 Grupo a analizar", grupos_disponibles)
        if st.button("✅ Cargar grupo", use_container_width=True, type="primary"):
            texto_grupo = dividir_grupos(texto_torneo).get(grupo_sel, "")
            eq, jug, pen = parsear_resultados(texto_grupo)
            if len(eq) >= 3:
                cargar_estado(eq, jug, pen)
                st.rerun()
            else:
                st.error("No se detectaron suficientes equipos.")

    if st.session_state.ESTADO:
        E = st.session_state.ESTADO
        st.divider()
        st.success(f"Grupo cargado · {len(E['equipos'])} equipos · {len(E['esc'])} escenarios")
        st.caption(f"Máx goles/equipo: {E['mg']} · Pendientes: {len(E['pendientes'])}")

# ─── MAIN TABS ─────────────────────────────────────────────────────────────────

if not st.session_state.ESTADO:
    st.info("👈 Cargá un grupo desde el panel lateral para comenzar el análisis.")
    st.stop()

E = st.session_state.ESTADO
equipos  = E["equipos"]
jugados  = E["jugados"]
pendientes = E["pendientes"]
esc      = E["esc"]

tabs = st.tabs([
    "📊 Tabla y panorama",
    "❓ ¿Qué necesita?",
    "🎯 Puesto puntual",
    "🔀 ¿Qué pasa si...?",
    "🧮 Simular resultado",
    "🎲 Probabilidades",
    "📈 Distribución",
    "🟰 ¿Qué le conviene?",
    "🏆 Cuentas de liga",
])

# ── Tab 0: Tabla y panorama ────────────────────────────────────────────────────
with tabs[0]:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Tabla actual")
        st.dataframe(tabla(equipos, jugados), use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Panorama de clasificación")
        st.dataframe(panorama(equipos, jugados, esc), use_container_width=True, hide_index=True)
    if pendientes:
        st.caption("Partidos pendientes: " + " · ".join(f"{l} vs {v}" for l, v in pendientes))

# ── Tab 1: Qué necesita ───────────────────────────────────────────────────────
with tabs[1]:
    st.subheader("❓ ¿Qué necesita un equipo?")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        eq_sel = st.selectbox("Equipo", equipos, key="nec_eq")
    with col2:
        obj_map = {
            "Reporte completo": "full",
            "Ser campeón (1º)": "campeon",
            "Clasificar (top N)": "top",
            "Quedar al menos 3º": "top3",
        }
        obj_label = st.selectbox("Situación", list(obj_map.keys()), key="nec_obj")
        obj = obj_map[obj_label]
    with col3:
        n_val = st.number_input("N", min_value=1, max_value=10, value=2, key="nec_n",
                                disabled=obj != "top")

    if not pendientes:
        st.info("No hay partidos pendientes en este grupo.")
    else:
        s = situacion(eq_sel, esc)
        if obj == "full":
            if s["ya_directo"]:
                st.success(f"🟢 **{eq_sel} ya clasificó directo** (siempre entre los 2 primeros).")
            elif s["eliminado"]:
                st.error(f"🔴 **{eq_sel} está eliminado** en todos los escenarios.")
            else:
                st.info(f"Puede terminar entre **{s['mejor']}º** y **{s['peor']}º**. "
                        f"Clasifica directo en {s['ndir']}/{s['total']} escenarios.")
            st.markdown("---")
            if not s["eliminado"] and not s["ya_directo"]:
                st.markdown(f"**Para clasificar directo:**\n\n" + que_necesita_texto(eq_sel, esc, pendientes, "directo"))
            if s["puede_1"] and not s["ya_1"]:
                st.markdown("---")
                st.markdown(f"**Para ser campeón:**\n\n" + que_necesita_texto(eq_sel, esc, pendientes, "campeon"))
        else:
            texto = que_necesita_texto(eq_sel, esc, pendientes, obj, n=n_val)
            st.markdown(texto)

# ── Tab 2: Puesto puntual ─────────────────────────────────────────────────────
with tabs[2]:
    st.subheader("🎯 ¿Qué resultados necesita para terminar en un puesto puntual?")
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        eq_p = st.selectbox("Equipo", equipos, key="pues_eq")
    with col2:
        puesto_n = st.selectbox("Puesto", list(range(1, len(equipos)+1)), index=1, key="pues_n",
                                format_func=lambda x: f"{x}º")
    with col3:
        modo_p = st.radio("Modo", ["Exactamente ese puesto", "Ese puesto o mejor"],
                          key="pues_modo", horizontal=True)

    if not pendientes:
        st.info("No hay partidos pendientes.")
    else:
        obj_p = ("exacto", puesto_n) if "Exactamente" in modo_p else ("al_menos", puesto_n)
        resultado = resultados_para_puesto_texto(eq_p, esc, pendientes, obj_p)
        st.markdown(resultado)

# ── Tab 3: Qué pasa si ───────────────────────────────────────────────────────
with tabs[3]:
    st.subheader("🔀 ¿Qué pasa si…? Fijá resultados y mirá cómo queda el grupo")
    if not pendientes:
        st.info("No hay partidos pendientes.")
    else:
        condiciones = []
        cols = st.columns(min(len(pendientes), 3))
        for i, (l, v) in enumerate(pendientes):
            with cols[i % 3]:
                cond = st.selectbox(
                    f"{l} vs {v}",
                    options=[None, "L", "E", "V"],
                    format_func=lambda x, l=l, v=v: {None: "(cualquiera)", "L": f"gana {l}", "E": "empate", "V": f"gana {v}"}[x],
                    key=f"qps_{i}"
                )
                condiciones.append(cond)
        sub, resumen = que_pasa_si(esc, pendientes, condiciones, equipos)
        st.caption(f"{len(sub)} escenarios cumplen esa condición.")
        st.dataframe(resumen, use_container_width=True, hide_index=True)

# ── Tab 4: Simular resultado ──────────────────────────────────────────────────
with tabs[4]:
    st.subheader("🧮 Simular un resultado puntual")
    if not pendientes:
        st.info("No hay partidos pendientes.")
    else:
        resultados_sim = []
        for i, (l, v) in enumerate(pendientes):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 0.5, 1, 3])
            with col1: st.markdown(f"**{l}**")
            with col2: gl = st.number_input("", min_value=0, max_value=20, value=0, key=f"sim_gl_{i}", label_visibility="collapsed")
            with col3: st.markdown("<div style='text-align:center;padding-top:8px'>–</div>", unsafe_allow_html=True)
            with col4: gv = st.number_input("", min_value=0, max_value=20, value=0, key=f"sim_gv_{i}", label_visibility="collapsed")
            with col5: st.markdown(f"**{v}**")
            resultados_sim.append((gl, gv))
        if st.button("Ver resultado", type="primary"):
            desc = texto_resultados(pendientes, resultados_sim)
            st.caption(f"Resultado simulado: {desc}")
            df_sim = simular(equipos, jugados, pendientes, resultados_sim)
            st.dataframe(df_sim, use_container_width=True, hide_index=True)

# ── Tab 5: Probabilidades ─────────────────────────────────────────────────────
with tabs[5]:
    st.subheader("🎲 Probabilidades estimadas (modelo Poisson)")
    st.caption("Modelo simple y neutral — orientativo, no oficial.")
    col1, col2 = st.columns(2)
    with col1:
        media_goles = st.slider("Goles promedio por equipo", 0.5, 3.0, 1.3, 0.1)
    with col2:
        n_sim = st.number_input("Simulaciones", min_value=1000, max_value=50000, value=8000, step=1000)
    if st.button("Estimar probabilidades", type="primary"):
        if not pendientes:
            st.info("No hay partidos pendientes — el resultado ya está determinado.")
            st.dataframe(tabla(equipos, jugados), use_container_width=True, hide_index=True)
        else:
            with st.spinner("Simulando…"):
                df_prob = probabilidades(equipos, jugados, pendientes, n=n_sim, media=media_goles)
            st.dataframe(df_prob, use_container_width=True, hide_index=True)

# ── Tab 6: Distribución ───────────────────────────────────────────────────────
with tabs[6]:
    st.subheader("📈 Distribución de puestos y casos extremos")
    st.markdown("En cuántos escenarios cae cada equipo en cada puesto:")
    st.dataframe(distribucion(equipos, esc), use_container_width=True)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        eq_dist = st.selectbox("Equipo", equipos, key="dist_eq")
    with col2:
        cual_ext = st.radio("Ver caso", ["Mejor", "Peor"], horizontal=True, key="dist_cual")
    if pendientes:
        mejor_bool = cual_ext == "Mejor"
        pos_col = esc[f"Pos {eq_dist}"]
        idx = pos_col.idxmin() if mejor_bool else pos_col.idxmax()
        row = esc.loc[idx]
        res_ext = [(int(row[f"P{i}_gl"]), int(row[f"P{i}_gv"])) for i in range(1, len(pendientes)+1)]
        puesto_ext = int(pos_col.loc[idx])
        st.info(f"**{cual_ext} caso para {eq_dist}:** termina {puesto_ext}º\n\n{texto_resultados(pendientes, res_ext)}")
        st.dataframe(simular(equipos, jugados, pendientes, res_ext), use_container_width=True, hide_index=True)
    else:
        st.info("No hay partidos pendientes.")

# ── Tab 7: Qué le conviene ────────────────────────────────────────────────────
with tabs[7]:
    st.subheader("🟰 ¿Qué le conviene a cada equipo?")
    st.caption("El resultado propio ordenado de mejor a peor para su clasificación.")
    if not pendientes:
        st.info("No hay partidos pendientes.")
    else:
        eq_conv = st.selectbox("Equipo", equipos, key="conv_eq")
        texto_conv = mejor_resultado_texto(eq_conv, esc, pendientes)
        st.markdown(texto_conv)

# ── Tab 8: Cuentas de liga ────────────────────────────────────────────────────
with tabs[8]:
    st.subheader("🏆 Cuentas de liga — puntos máximos y número mágico")
    col1, col2 = st.columns(2)
    with col1:
        n_top = st.number_input("Top N (1 = campeón)", min_value=1, max_value=len(equipos)-1, value=1)
    with col2:
        eq_mag = st.selectbox("Equipo para número mágico", equipos, key="liga_eq")

    st.markdown("**Puntos máximos posibles:**")
    st.dataframe(maximos_minimos(equipos, jugados, pendientes), use_container_width=True, hide_index=True)
    st.markdown(f"**Asegurado / Sin chances (top {n_top}):**")
    st.dataframe(clasificado_eliminado(equipos, jugados, pendientes, n_top), use_container_width=True, hide_index=True)
    st.markdown("**Número mágico:**")
    st.markdown(numero_magico_texto(eq_mag, equipos, jugados, pendientes, n_top))
