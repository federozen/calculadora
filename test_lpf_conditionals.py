from lpf_conditionals import next_round_conditionals


def _base():
    return {
        "A": {"pts": 10}, "B": {"pts": 10}, "C": {"pts": 9}, "D": {"pts": 7},
    }


def test_conditionals_enumerates_only_relevant_matches_and_keeps_interzonal():
    report = next_round_conditionals(
        _base(), {"A": 1, "B": 1, "C": 1, "D": 1},
        [("A", "X"), ("B", "C"), ("Y", "Z")], "A", cutoff=2,
    )
    assert report["available"] is True
    assert report["own_match"] == ("A", "X")
    assert report["other_matches"] == [("B", "C")]
    assert all(branch["total_combinations"] == 3 for branch in report["branches"])


def test_conditionals_branch_can_be_independent_of_other_results():
    base = {"A": {"pts": 10}, "B": {"pts": 7}, "C": {"pts": 5}, "D": {"pts": 4}}
    report = next_round_conditionals(
        base, {team: 1 for team in base}, [("A", "X"), ("B", "C")], "A", cutoff=2,
    )
    win = report["branches"][0]
    assert win["season_in"] == win["total_combinations"]
    assert win["sufficient_condition"] == "No depende de otros resultados"


def test_conditionals_finds_simple_sufficient_other_result():
    base = {"A": {"pts": 8}, "B": {"pts": 10}, "C": {"pts": 8}, "D": {"pts": 4}}
    report = next_round_conditionals(
        base, {team: 1 for team in base}, [("A", "X"), ("B", "C")], "A", cutoff=2,
    )
    draw = next(branch for branch in report["branches"] if branch["result"] == "E")
    assert draw["round_safe"] > 0
    assert draw["sufficient_condition"] is not None


def test_conditionals_frequency_is_not_exposed_as_probability():
    report = next_round_conditionals(
        _base(), {team: 2 for team in _base()}, [("A", "D"), ("B", "C")], "A", cutoff=2,
    )
    assert "no es una probabilidad" in report["frequency_note"].lower()
    for branch in report["branches"]:
        assert "probability" not in branch
        assert branch["season_in"] + branch["season_pelea"] + branch["season_out"] == branch["total_combinations"]
