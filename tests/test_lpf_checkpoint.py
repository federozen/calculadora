from collections import Counter
from copy import deepcopy

from lpf_checkpoint import (checkpoint_zones, checkpoint_results,
                            project_checkpoint, save_recent_results, cached_results)
from lpf_data_2026 import LPF_FIXTURE, TABLA_ANUAL_LPF_2026
from lpf_parsers import parse_tabla_anual
from lpf_data_quality import derive_opening_from_results
from lpf_data_quality import fixture_records, pending_pairs
from lpf_loading import prepare_automatic_update, prepare_offline_load
from lpf_reconcile import _lpf_results_fit_zones
from lpf_state import build_lpf_state
from lpf_fixture_sources import parse_lpf_official_results_article_html, played_pending_from_records
from lpf_clubs import canon_club

LPF_APERTURA_BASE_2026, _ = derive_opening_from_results(
    parse_tabla_anual(TABLA_ANUAL_LPF_2026)[0], LPF_FIXTURE,
    [r for r in checkpoint_results() if (r[0], r[1]) in
     {(g['l'], g['v']) for g in LPF_FIXTURE if g['f'] == 1}], opening_rounds=16)


def test_fixed_150_results_reproduce_all_30_rows():
    fixed = checkpoint_results()
    assert len(fixed) == len({(h, a) for h, a, _, _ in fixed}) == 150
    assert _lpf_results_fit_zones(checkpoint_zones(), fixed)
    assert {r['pj'] for z in checkpoint_zones().values() for r in z.values()} == {10}


def test_partial_round_and_repeated_update_do_not_double_count():
    result = ('Boca Juniors', 'Unión', 3, 0)
    first = prepare_automatic_update(checkpoint_zones(), official_played=[result],
                                     opening=LPF_APERTURA_BASE_2026, use_checkpoint=True)
    second = prepare_automatic_update(first['zones'], previous_played=first['played'],
                                      official_played=[result], use_checkpoint=True)
    assert first['zones'] == second['zones']
    assert first['zones']['A']['Boca Juniors']['pj'] == 11
    assert first['zones']['A']['Boca Juniors']['pts'] == 20
    assert len(second['played']) == 151
    state, report = build_lpf_state(first['zones'], played=first['played'],
                                    builtin_opening=LPF_APERTURA_BASE_2026, fixture=LPF_FIXTURE)
    assert not any(i.domain == 'data' and i.level == 'blocked' for i in report.issues)
    assert len(state['pendientes']) == 89
    assert ('Sarmiento', 'River Plate') in state['pendientes']
    assert state['anual_directo']['Boca Juniors']['pj'] == 27


def test_empty_network_and_restart_keep_new_results(tmp_path):
    result = ('Defensa y Justicia', 'San Lorenzo', 3, 0)
    path = tmp_path / 'recent.json'
    save_recent_results([result], path)
    restored = checkpoint_results() + cached_results(path)
    prepared = prepare_automatic_update(checkpoint_zones(), builtin_played=restored,
                                         use_checkpoint=True)
    offline = prepare_offline_load(checkpoint_zones(), builtin_played=restored,
                                    use_checkpoint=True)
    assert prepared['zones'] == offline['zones']
    assert prepared['zones']['A']['Defensa y Justicia']['pts'] == 21
    assert len(prepared['played']) == 151


def test_missing_old_history_is_safe_only_when_all_totals_match_cut():
    played = [('Boca Juniors', 'Unión', 3, 0)]
    zones = project_checkpoint(played)
    records, issues = fixture_records(LPF_FIXTURE, played, zones)
    assert Counter(r.status for r in records) == {'played': 1, 'unconfirmed': 150, 'scheduled': 89}
    assert not any(i.level == 'blocked' for i in issues)
    broken = deepcopy(zones)
    broken['A']['Boca Juniors']['pts'] += 1
    _, issues = fixture_records(LPF_FIXTURE, played, broken)
    assert any(i.level == 'blocked' for i in issues)


def test_old_network_scores_cannot_modify_the_fixed_base():
    old = checkpoint_results()[0]
    changed = (*old[:2], 99, 0)
    prepared = prepare_automatic_update(checkpoint_zones(), official_played=[changed],
                                         use_checkpoint=True)
    assert prepared['zones'] == checkpoint_zones()
    assert _lpf_results_fit_zones(prepared['zones'], prepared['played'])


def test_live_lpf_content_ignores_related_articles_and_in_progress_score():
    html = '''<div class="elementor-widget-theme-post-content">
    <p>Fecha 11<br>Boca 3 – Unión 0 (Zona A)<br>
    En juego Huracán 1 – Aldosivi 0 (Zona B)</p></div>
    <article><p>Fecha 11<br>Vélez 9 – Platense 0</p></article>'''
    records = parse_lpf_official_results_article_html(
        html, canon_club=canon_club, official_fixture=LPF_FIXTURE, expected_round=11)
    played, _ = played_pending_from_records(records)
    assert played == [('Boca Juniors', 'Unión', 3, 0)]
