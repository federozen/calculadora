"""Informe editorial por fecha, sin red ni interfaz; distingue previa y foto actual."""
from __future__ import annotations
from lpf_checkpoint import CHECKPOINT_ROUND, checkpoint_results, project_checkpoint
from lpf_clubs import canon_club
from lpf_conditionals import _season_state
from lpf_display import editorialize_text
from lpf_schedule import format_datetime
from lpf_standings import liga_tabla_df

LPF_RUNTIME_API = 21


def round_start_snapshot(played, fixture, round_no):
    """Sólo reconstruye una previa cuando todas las fechas anteriores están cerradas."""
    round_no = int(round_no)
    if round_no <= CHECKPOINT_ROUND:
        return {'available': False, 'reason': 'La reconstrucción de previas comienza en la fecha 11.'}
    rounds = {(g['l'], g['v']): int(g['f']) for g in fixture}
    known = {(h, a): (int(gh), int(ga)) for h, a, gh, ga in checkpoint_results()}
    for h, a, gh, ga in played or []:
        pair = (canon_club(h), canon_club(a))
        if pair not in rounds:
            return {'available': False, 'reason': 'Hay resultados fuera del fixture oficial.'}
        score = (int(gh), int(ga))
        if rounds[pair] > CHECKPOINT_ROUND and pair in known and known[pair] != score:
            return {'available': False, 'reason': 'Hay marcadores contradictorios: no se reconstruye una previa.'}
        if min(score) < 0:
            return {'available': False, 'reason': 'Hay un marcador inválido.'}
        if rounds[pair] > CHECKPOINT_ROUND:
            known[pair] = score
    missing = [pair for pair, f in rounds.items() if f < round_no and pair not in known]
    if missing:
        return {'available': False, 'reason': f'Faltan {len(missing)} resultados anteriores a la fecha {round_no}. Usá el informe actualizado; no se inventa una foto previa.'}
    before = [(h, a, *score) for (h, a), score in known.items() if rounds[(h, a)] < round_no]
    zones = project_checkpoint(before, fixture)
    pending = [(g['l'], g['v']) for g in fixture if int(g['f']) >= round_no]
    return {'available': True, 'zones': zones, 'pending': pending, 'played': before}


def build_round_article(zones, pending, fixture, round_no, *, mode='before', played=(), schedule=None, cutoff=8):
    """Genera título, bajada, panorama, cruces y bloques de los 30 equipos.

    No convierte distancias al corte en garantías. La previa usa la foto de inicio;
    el informe actualizado identifica los partidos ya terminados de esta fecha.
    """
    schedule = schedule or {}
    round_no = int(round_no)
    pairs = [tuple(p) for p in pending]
    rounds = {(g['l'], g['v']): int(g['f']) for g in fixture}
    games = [p for p, f in rounds.items() if f == round_no]
    scores = {(canon_club(h), canon_club(a)): (int(gh), int(ga)) for h, a, gh, ga in played or []}
    all_rows = {t: row for base in zones.values() for t, row in base.items()}
    remaining = {t: sum(t in p for p in pairs) for t in all_rows}
    tables = {lab: liga_tabla_df(base) for lab, base in zones.items()}
    states = {t: _season_state({n: int(r.get('pts', 0)) for n, r in base.items()}, remaining, t, cutoff)
              for base in zones.values() for t in base}
    qualified = [editorialize_text(t) for t, s in states.items() if s == 'in']
    eliminated = [editorialize_text(t) for t, s in states.items() if s == 'out']
    counts = sorted(set(remaining.values()))
    left_text = (f'{counts[0]} partidos por equipo' if len(counts) == 1 else
                 f'entre {counts[0]} y {counts[-1]} partidos por equipo') if counts else 'sin partidos pendientes'
    if mode == 'before':
        protagonists = 'Boca, River y los otros 28 equipos' if len(all_rows) == 30 and {'Boca Juniors', 'River Plate'} <= set(all_rows) else f'los {len(all_rows)} equipos'
        title = f'Clausura: las cuentas de {protagonists} antes de la fecha {round_no}'
        scope = f'Foto previa al inicio de la fecha {round_no}, con todas las jornadas anteriores cerradas.'
    else:
        title = f'Clausura: las cuentas actuales de los 30 equipos y los cruces de la fecha {round_no}'
        scope = f'Foto actual de los datos cargados: incluye los finales confirmados de la fecha {round_no} y de otras jornadas.'
    finished = sum(p in scores for p in games)
    subtitle = f'Quedan {left_text}. La situación en las dos zonas, los cruces de la fecha y el fixture de cada equipo rumbo a los octavos.'
    intro = f'Clasifican los {cutoff} primeros de cada zona. '
    intro += ('Garantías comprobadas por puntos y techos restantes: ' + ', '.join(qualified) + '. ') if qualified else 'La comprobación por puntos y techos restantes todavía no marca clasificados. '
    intro += ('Sin chances por ese criterio: ' + ', '.join(eliminated) + '. ') if eliminated else 'La comprobación por puntos y techos restantes todavía no marca eliminados. '
    if mode != 'before':
        intro += f'Esta fecha tiene {finished} de {len(games)} partidos con resultado final confirmado. '
    intro += 'Estar entre los ocho hoy no equivale a tener el pase asegurado; la distancia al corte es una referencia actual y puede cambiar.'
    key_matches = []
    for h, a in games:
        finished_note = ' (ya finalizado)' if mode != 'before' and (h, a) in scores else ''
        lab = next((lab for lab, base in zones.items() if h in base and a in base), None)
        if lab is None:
            key_matches.append(f'{editorialize_text(h)}–{editorialize_text(a)}{finished_note}: interzonal, suma en dos zonas distintas.')
            continue
        table = tables[lab]
        order = list(table['Equipo'])
        hp, ap = order.index(h)+1, order.index(a)+1
        if abs(hp-cutoff) <= 2 or abs(ap-cutoff) <= 2 or abs(int(all_rows[h]['pts'])-int(all_rows[a]['pts'])) <= 3:
            key_matches.append(f'{editorialize_text(h)}–{editorialize_text(a)}{finished_note}: {hp}º contra {ap}º en la zona {lab}, con {all_rows[h]["pts"]} y {all_rows[a]["pts"]} puntos en esta foto.')
    blocks = []
    for lab, table in tables.items():
        base = zones[lab]
        cut_team = table.iloc[min(cutoff, len(table))-1]['Equipo']
        cut_pts = int(base[cut_team]['pts'])
        outside_team = table.iloc[cutoff]['Equipo'] if len(table) > cutoff else None
        outside_pts = int(base[outside_team]['pts']) if outside_team else None
        for row in table.to_dict('records'):
            t, pos, pts, pj = row['Equipo'], int(row['Pos']), int(row['PTS']), int(row['PJ'])
            left, state = remaining[t], states[t]
            if state == 'in':
                situation = 'Tiene asegurado el lugar en los octavos aun con desempate adverso.'
            elif state == 'out':
                situation = f'No puede entrar por puntos: hay al menos {cutoff} rivales fuera de su alcance.'
            elif pos <= cutoff and outside_pts is not None:
                gap = pts-outside_pts
                situation = (f'Está dentro de los ocho y le lleva {gap} puntos al {cutoff+1}º, {editorialize_text(outside_team)}.' if gap else
                             f'Está dentro de los ocho, igualado en puntos con {editorialize_text(outside_team)}; hoy los separa el desempate.')
                situation += ' Esa posición todavía no asegura la clasificación.'
            else:
                gap = cut_pts-pts
                situation = (f'Está a {gap} puntos del {cutoff}º, {editorialize_text(cut_team)}.' if gap else
                             f'Iguala en puntos al {cutoff}º, {editorialize_text(cut_team)}, pero hoy queda afuera por el desempate.')
                situation += ' Alcanzar ese puntaje no garantiza entrar: también puede moverse la línea de clasificación.'
            own = next((p for p in games if t in p), None)
            this_round = 'Sin partido identificado en esta fecha.'
            crossing = ''
            if own:
                h, a = own
                rival = a if h == t else h
                venue = 'recibe a' if h == t else 'visita a'
                when = format_datetime(str(schedule.get(own) or ''))
                this_round = f'{venue.capitalize()} {editorialize_text(rival)}' + (f', {when} (hora argentina).' if when else '. Horario no disponible en la programación cargada.')
                if mode != 'before' and own in scores:
                    gh, ga = scores[own]
                    this_round = f'Ya terminó: {editorialize_text(h)} {gh}–{ga} {editorialize_text(a)}.'
                elif rival in base:
                    diff = pts-int(base[rival]['pts'])
                    crossing = (f'Contra su rival de esta fecha, la diferencia de puntos pasa a {diff+3:+d} si gana, '
                                f'{diff:+d} si empata y {diff-3:+d} si pierde. El signo positivo indica ventaja; el negativo, desventaja. '
                                'Esa cuenta no determina por sí sola el puesto ni la clasificación.')
            own_pending = sorted((p for p in pairs if t in p), key=lambda p: rounds.get(p, 99))
            fixture_text = ', '.join(f'F{rounds.get(p, "?")}: {editorialize_text(p[1] if p[0] == t else p[0])} ({"L" if p[0] == t else "V"})' for p in own_pending)
            blocks.append({'zone': lab, 'team': t, 'objective_state': state, 'points': pts, 'position': pos, 'heading': f'{editorialize_text(t)}: {pts} puntos, {pos}º',
                           'situation': situation, 'games_played': pj, 'remaining': left, 'ceiling': pts+3*left,
                           'this_round': this_round, 'crossing': crossing, 'fixture': fixture_text or 'Sin partidos pendientes.'})
    lines = [f'# {title}', subtitle, scope, intro]
    if key_matches:
        lines += ['## Cruces para seguir', *[f'- {s}' for s in key_matches]]
    for lab in tables:
        lines.append(f'## Zona {lab}')
        for b in blocks:
            if b['zone'] != lab:
                continue
            lines += [f'### {b["heading"]}', b['situation'],
                      f'Tiene {b["games_played"]} partidos jugados, {b["remaining"]} por jugar y un techo de {b["ceiling"]} puntos.',
                      f'**Esta fecha:** {b["this_round"]}']
            if b['crossing']: lines.append(b['crossing'])
            lines.append(f'**Lo que le queda:** {b["fixture"]}')
    lines.append('L = local; V = visitante. El techo supone ganar todos los partidos pendientes y no es una proyección. '
                 'Los estados de garantía y eliminación se prueban por puntos y techos restantes; que el criterio no cierre el objetivo no demuestra que exista un cierre favorable del fixture completo.')
    return {'title': title, 'subtitle': subtitle, 'scope': scope, 'intro': intro,
            'key_matches': key_matches, 'teams': blocks, 'text': '\n\n'.join(lines)}


def build_editorial_piece(article, kind, team, *, previous=None):
    """Formatos breves que reutilizan hechos calculados y no agregan pronósticos."""
    selected = next((b for b in article['teams'] if b['team'] == team), None)
    if selected is None:
        raise ValueError('Equipo fuera de la foto')
    cards = []
    if kind == 'Tarjeta del equipo':
        title = f'{editorialize_text(team)}: las cuentas en 30 segundos'
        cards = [
            {'title': selected['heading'], 'body': selected['situation']},
            {'title': 'Esta fecha', 'body': selected['this_round']},
            {'title': 'Lo que le queda', 'body': selected['fixture']},
            {'title': 'Su máximo posible', 'body': f"{selected['remaining']} partidos por jugar; techo de {selected['ceiling']} puntos. Supone ganar todo y no es una proyección."},
        ]
    elif kind == 'Duelos de la fecha':
        title = 'Los cruces que mueven la pelea'
        cards = [{'title': 'Cruce de la fecha', 'body': s} for s in article['key_matches']]
        if not cards:
            cards = [{'title': 'Sin cruces destacados', 'body': 'No hay un cruce directo identificado por cercanía al corte o por diferencia de hasta tres puntos en esta foto.'}]
    elif kind == 'Radiografía de la zona':
        title = f"Zona {selected['zone']}: quién está adentro y quién viene detrás"
        cards = [{'title': b['heading'], 'body': b['situation']} for b in article['teams'] if b['zone'] == selected['zone']]
    elif kind == 'Semáforo de playoffs':
        title = 'Playoffs: asegurados, eliminados y pelea abierta'
        labels = {'in': 'ASEGURA', 'out': 'ELIMINADO', 'pelea': 'ABIERTO'}
        cards = [{'title': f"{editorialize_text(b['team'])} · {labels[b['objective_state']]}",
                  'body': b['situation'], 'state': b['objective_state']} for b in article['teams']]
    elif kind == 'Antes y después de la fecha':
        if previous is None:
            raise ValueError('No hay una foto previa completa para comparar')
        before = next(b for b in previous['teams'] if b['team'] == team)
        title = f'{editorialize_text(team)}: qué cambió desde el inicio de la fecha'
        cards = [
            {'title': 'Antes', 'body': f"{before['points']} puntos, {before['position']}º; {before['remaining']} partidos por jugar."},
            {'title': 'Ahora', 'body': f"{selected['points']} puntos, {selected['position']}º; {selected['remaining']} partidos por jugar."},
            {'title': 'La diferencia', 'body': f"Tiene {selected['points']-before['points']:+d} puntos respecto de esa foto. La posición también puede cambiar por resultados de otras canchas."},
            {'title': 'Qué sigue', 'body': selected['fixture']},
        ]
    else:
        raise ValueError('Formato desconocido')
    note = ('Foto de los datos cargados. El semáforo de garantía usa puntos y techos restantes; estar dentro hoy no equivale a asegurar. '
            'Un objetivo abierto no demuestra por sí solo un cierre favorable del fixture completo. Las piezas no incluyen probabilidades.')
    text = '\n\n'.join([f'# {title}', article['scope'], *[f"## {c['title']}\n\n{c['body']}" for c in cards], note])
    return {'title': title, 'scope': article['scope'], 'cards': cards, 'note': note, 'text': text}


def piece_html(piece):
    """HTML autónomo, sin imágenes, scripts ni fuentes externas."""
    from html import escape
    palette = {'in': '#15803d', 'out': '#b91c1c', 'pelea': '#b45309'}
    cards = ''.join(f'<article class="card" style="border-top-color:{palette.get(c.get("state"), "#2563eb")}">'
                    f'<h2>{escape(c["title"])}</h2><p>{escape(c["body"])}</p></article>' for c in piece['cards'])
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(piece["title"])}</title><style>'
            'body{margin:0;background:#f1f5f9;color:#0f172a;font:17px/1.55 system-ui,sans-serif;padding:20px}'
            'main{max-width:1000px;margin:auto}h1{font-size:clamp(24px,4vw,36px);line-height:1.2}'
            '.scope,footer{color:#475569;font-size:14px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:16px}'
            '.card{background:#fff;border-radius:12px;border-top:5px solid;padding:20px;box-shadow:0 2px 8px #0f172a12}'
            '.card h2{font-size:20px;margin:0 0 10px}.card p{margin:0}footer{margin-top:20px}'
            '</style></head><body><main>' + f'<h1>{escape(piece["title"])}</h1><p class="scope">{escape(piece["scope"])}</p>'
            f'<section class="grid">{cards}</section><footer>{escape(piece["note"])}</footer></main></body></html>')


def playoff_bracket(zones):
    """Octavos de hoy, con orden del art. 14.2 y localía del art. 14.2.1."""
    if not {'A','B'} <= set(zones):
        raise ValueError('Se necesitan las zonas A y B')
    tables = {z: liga_tabla_df(zones[z]).to_dict('records') for z in ('A','B')}
    if min(map(len,tables.values())) < 8:
        raise ValueError('Se necesitan ocho equipos por zona')
    rows=[]
    for pos in range(1,5):
        for home_zone, away_zone in [('A','B'),('B','A')]:
            home=tables[home_zone][pos-1];away=tables[away_zone][8-pos]
            rows.append({'Partido':len(rows)+1, 'Local':home['Equipo'], 'Visitante':away['Equipo'],
                         'Puesto local':f'{pos}º {home_zone}', 'Puesto visitante':f'{9-pos}º {away_zone}',
                         'Puntos local':int(home['PTS']), 'Puntos visitante':int(away['PTS'])})
    return rows


def fixture_difficulty(zones, pending, *, venue_percent=10):
    """Índice editorial reproducible, no modelo de probabilidad ni pronóstico.

    Promedio de PPJ rivales, multiplicado por 1 +/- peso de localía por partido.
    El peso es una decisión editorial explícita; cero da comparación neutral.
    Sin PJ de un rival, el equipo no recibe un índice completo ni puesto.
    """
    if not 0 <= float(venue_percent) <= 30:
        raise ValueError('Peso de localía fuera de rango')
    base={t:r for b in zones.values() for t,r in b.items()}
    games=list(dict.fromkeys(tuple(p) for p in pending))
    weight=float(venue_percent)/100
    rows=[]
    for t in base:
        own=[p for p in games if t in p]
        values=[];adjusted=[];detail=[];missing=[]
        for h,a in own:
            rival=a if h==t else h
            row=base.get(rival) or {}
            pj=int(row.get('pj',0))
            if pj<=0:
                missing.append(rival)
                detail.append(f'{editorialize_text(rival)} ({"L" if h==t else "V"}) · sin PJ')
                continue
            ppg=int(row.get('pts',0))/pj
            values.append(ppg)
            adjusted.append(ppg*(1-weight if h==t else 1+weight))
            detail.append(f'{editorialize_text(rival)} ({"L" if h==t else "V"}) · {ppg:.2f} PPJ')
        score=sum(adjusted)/len(own) if own and not missing else None
        rows.append({'Equipo':t,'Pendientes':len(own),'Locales':sum(h==t for h,a in own),
                     'Visitantes':sum(a==t for h,a in own),'PPJ rivales':sum(values)/len(own) if own and not missing else None,
                     'Índice':score,'Carga total':sum(adjusted) if own and not missing else None,
                     'Rivales':'; '.join(detail),'Estado':'Faltan PJ de rivales' if missing else 'Sin partidos pendientes' if not own else 'Completo'})
    rows.sort(key=lambda r:(r['Índice'] is None,-(r['Índice'] or 0),r['Equipo']))
    last=None;rank=None
    for i,row in enumerate(rows,1):
        value=row['Índice']
        if value is not None:
            if last is None or abs(value-last)>1e-10:rank=i
            last=value
        row['Orden']=rank if value is not None else None
        for key in ('PPJ rivales','Índice','Carga total'):
            if row[key] is not None:row[key]=round(row[key],3)
    return rows


def cut_neighbors(article, team, cutoff=8):
    selected=next(b for b in article['teams'] if b['team']==team)
    return [b for b in article['teams'] if b['zone']==selected['zone'] and b['position'] in (cutoff-1,cutoff,cutoff+1)]



def build_fixture_piece(article, kind, team, zones, pending, fixture, round_no, *, venue_percent=10):
    """Cuatro piezas con alcance explícito y exportación de los mismos hechos."""
    cards=[]; report=None
    if kind == 'Cruces de octavos':
        title='Los octavos si terminara hoy'
        for r in playoff_bracket(zones):
            cards.append({'title': f"Partido {r['Partido']}: {editorialize_text(r['Local'])} – {editorialize_text(r['Visitante'])}",
                          'body': f"{r['Puesto local']} contra {r['Puesto visitante']}. Local: {editorialize_text(r['Local'])}. Puntos actuales: {r['Puntos local']} y {r['Puntos visitante']}."})
        cards.append({'title':'Camino a cuartos', 'body':'Los ganadores se cruzan así: partido 1 con 8, 2 con 7, 3 con 6 y 4 con 5.'})
        note='Foto actual, no cruces confirmados ni pronóstico. Reglamento LPF 2026, artículos 14.2, 14.2.1 y 14.3. Orden sujeto a los desempates de la tabla cargada.'
    elif kind == 'Dificultad del fixture':
        title='Quién tiene el camino restante más exigente'
        for r in fixture_difficulty(zones,pending,venue_percent=venue_percent):
            label=f"{r['Orden']}º · " if r['Orden'] is not None else ''
            body=(f"Índice {r['Índice']:.3f}; PPJ medio de rivales {r['PPJ rivales']:.3f}. " if r['Índice'] is not None else r['Estado']+'. ')
            body+=f"{r['Pendientes']} pendientes: {r['Locales']} de local y {r['Visitantes']} de visitante. " + r['Rivales']
            cards.append({'title':label+editorialize_text(r['Equipo']), 'body':body})
        note=f'Índice editorial: promedio de puntos por partido (PPJ) de los rivales pendientes, con reducción del {venue_percent}% al jugar de local y aumento del {venue_percent}% al visitar. Ajuste elegido para esta comparación, no calibrado estadísticamente. Mayor índice = rivales más exigentes según esta medida. No estima resultados ni probabilidades. Se promedia por partido para comparar calendarios de distinto largo; L/V es la localía del equipo analizado. Empates comparten puesto; el orden usa valores sin redondear.'
    elif kind == 'La pelea del 7º, 8º y 9º':
        neighbors=cut_neighbors(article,team)
        title=f"Zona {neighbors[0]['zone']}: tres puestos alrededor del corte"
        for b in neighbors:
            cards.append({'title':b['heading'], 'body':f"{b['situation']} Le quedan {b['remaining']} partidos; su techo es {b['ceiling']} puntos. Esta fecha: {b['this_round']} Fixture: {b['fixture']}"})
        note='Clasifican ocho por zona. El techo supone ganar todo; no es un puntaje proyectado. La distancia actual puede cambiar y una igualdad puede requerir desempate.'
    elif kind == 'Qué puede definirse esta fecha':
        from lpf_conditionals import next_round_conditionals
        selected=next(b for b in article['teams'] if b['team']==team)
        base=zones[selected['zone']]
        rest={t:sum(t in p for p in pending) for t in base}
        round_pairs={(g['l'],g['v']) for g in fixture if int(g['f'])==int(round_no)}
        games=[tuple(p) for p in pending if tuple(p) in round_pairs]
        report=next_round_conditionals(base,rest,games,team,8,max_other_matches=8)
        title=f"{editorialize_text(team)}: qué puede definirse en la fecha {round_no}"
        cards.append({'title':'Punto de partida', 'body':selected['situation']+' '+selected['this_round']})
        if not report.get('available'):
            cards.append({'title':'Análisis de ramas no disponible', 'body':report['reason']+' Los partidos finalizados ya están incorporados a la foto actual.'})
        else:
            for b in report['branches']:
                total=b['total_combinations']
                if b['season_in']==total:
                    body='Asegura los playoffs con cualquier combinación de las otras canchas.'
                elif b['season_in']:
                    body=f"Puede asegurar: {b['season_in']} de {total} combinaciones ajenas cumplen el criterio. Revisá todas las condiciones debajo."
                else:
                    body='Ninguna combinación ajena asegura el pase con el criterio de puntos y techos restantes.'
                body+=f" Queda eliminado por ese criterio en {b['season_out']} de {total} combinaciones; la comprobación sigue abierta en {b['season_pelea']}. Termina esta fecha adentro sin desempate en {b['round_safe']}, empatado en la línea en {b['round_tiebreak']} y afuera en {b['round_out']}."
                cards.append({'title':f"{b['result_label']}: {b['final_points_after_round']} puntos",'body':body})
        note='Todas las combinaciones G/E/P de los partidos pendientes de esta fecha que afectan a la zona. Los conteos son combinatorios, no probabilidades. Asegurar playoffs se distingue de terminar esta fecha adentro. El criterio de garantía usa puntos y techos con desempate adverso; abierto no prueba que exista un cierre favorable del fixture completo. Los postergados de otras fechas siguen contando como partidos restantes.'
    else:
        raise ValueError('Formato desconocido')
    text='\n\n'.join([f'# {title}',article['scope'],*[f"## {c['title']}\n\n{c['body']}" for c in cards],note])
    return {'title':title,'scope':article['scope'],'cards':cards,'note':note,'text':text,'report':report}



def build_need_piece(team, objective, result, *, scope='Foto actual de los datos cargados.'):
    """Tarjeta corta desde el contrato de cálculo; jamás deduce una garantía."""
    descent=objective=='Descenso'
    if descent and not result.get('complete'):
        raise ValueError(result.get('warning') or 'Faltan datos para comprobar ambas vías de descenso.')
    floor=(result.get('team') or {}) if descent else result
    cards=[]
    title=f'{editorialize_text(team)}: qué necesita para ' + ('asegurar la permanencia' if descent else objective.lower())
    if floor.get('resolved'):
        cards=[{'title':'Objetivo resuelto por otra vía', 'body':floor.get('message') or 'La plaza ya está confirmada por otra vía.', 'state':'in'}]
    else:
        current=int(floor.get('puntos_hoy',0));ceiling=int(floor.get('techo',current))
        state=floor.get('estado','pelea')
        exact=floor.get('minimum_guarantee')
        safe=floor.get('conservative_reference')
        minimum=floor.get('minimum_possible')
        if state=='in':
            summary=f'Ya asegura el objetivo con {current} puntos.'
        elif state=='out':
            summary=f'No puede alcanzar este objetivo por esta vía, aun llegando a su techo de {ceiling} puntos.'
        elif exact is not None:
            summary=f'Necesita sumar {max(0,int(exact)-current)} puntos para llegar al mínimo comprobado que asegura: {exact}.'
        elif safe is not None:
            summary=f'Un total seguro es {safe}: necesita sumar {max(0,int(safe)-current)} puntos. Puede alcanzar con menos; ese total no está comprobado como el mínimo.'
        elif floor.get('exacto'):
            summary=f'No existe un total alcanzable que asegure el objetivo por sí solo. Incluso con su techo de {ceiling} puntos queda al menos un cierre adverso.'
        else:
            summary='Todavía no hay un mínimo que asegure comprobado. Eso no equivale a estar eliminado.'
        cards.append({'title':'La respuesta corta','body':summary,'state':state})
        cards.append({'title':'Desde dónde parte', 'body':f'{current} puntos actuales; techo de {ceiling} ganando todo. El techo es un máximo, no una proyección.'})
        if minimum is not None and state=='pelea':
            help_text = ('Ese total también coincide con el mínimo que asegura comprobado.' if exact is not None and int(minimum)>=int(exact) else 'Comprueba que existe un cierre favorable; ese dato por sí solo no demuestra una garantía. Revisá las condiciones y los resultados ajenos.')
            cards.append({'title':'Con cuánto todavía puede alcanzar', 'body':f'El menor total posible comprobado es {minimum} puntos (sumar {max(0,int(minimum)-current)}). '+help_text})
        elif state=='pelea':
            cards.append({'title':'Qué falta comprobar', 'body':'El menor puntaje con un cierre favorable no está disponible en esta consulta. No se obtiene restando puntos al corte de hoy.'})
    if descent:
        note='Bajan por Tabla General y por promedios: hay que zafar de las dos. La comprobación usa ambas tablas y la regla de reasignación; la foto de hoy no es un descenso confirmado.'
    elif objective in ('Libertadores','Al menos Sudamericana'):
        note='Cuenta por Tabla Anual bajo los campeones y las plazas cargados. Al menos Sudamericana incluye conseguir Libertadores. Una garantía por esta tabla no anticipa los campeones pendientes ni todas las vías alternativas. Belgrano* ya tiene plaza por ser campeón del Apertura.'
    else:
        note='Clasifican ocho por zona. El mínimo que asegura y el menor total posible son cuentas diferentes; la posición actual no prueba una garantía.'
    text='\n\n'.join([f'# {title}',scope,*[f"## {c['title']}\n\n{c['body']}" for c in cards],note])
    return {'title':title,'scope':scope,'cards':cards,'note':note,'text':text,'floor':floor}
