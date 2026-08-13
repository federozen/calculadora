from lpf_relegation import current_relegation_picture


def test_unique_average_relegation_is_excluded_from_annual_route():
    annual = {"A": {"pts": 10}, "B": {"pts": 11}, "C": {"pts": 12}}
    averages = [
        {"Equipo": "A", "Pts": 100, "PJ": 100},
        {"Equipo": "B", "Pts": 90, "PJ": 100},
        {"Equipo": "C", "Pts": 120, "PJ": 100},
    ]
    pic = current_relegation_picture(annual, averages)
    assert pic["average_confirmed"] == ["B"]
    assert pic["annual_scenarios"][0]["annual_confirmed"] == ["A"]


def test_tie_for_average_relegation_is_reported_as_playoff():
    annual = {"A": {"pts": 10}, "B": {"pts": 11}, "C": {"pts": 12}}
    averages = [
        {"Equipo": "A", "Pts": 100, "PJ": 100},
        {"Equipo": "B", "Pts": 100, "PJ": 100},
        {"Equipo": "C", "Pts": 120, "PJ": 100},
    ]
    pic = current_relegation_picture(annual, averages)
    assert pic["average_confirmed"] == []
    assert set(pic["average_playoff"]) == {"A", "B"}
    assert pic["annual_depends_on_average_playoff"] is True


def test_tie_for_annual_relegation_is_not_broken_by_goal_difference():
    annual = {
        "A": {"pts": 10, "dg": -20},
        "B": {"pts": 10, "dg": 5},
        "C": {"pts": 14, "dg": -30},
    }
    pic = current_relegation_picture(annual, [], average_relegations=0)
    scenario = pic["annual_scenarios"][0]
    assert scenario["annual_confirmed"] == []
    assert set(scenario["annual_playoff"]) == {"A", "B"}


def test_equal_ratio_is_exact_not_rounded_decimal():
    annual = {"A": {"pts": 10}, "B": {"pts": 11}, "C": {"pts": 12}}
    averages = [
        {"Equipo": "A", "Pts": 2, "PJ": 3},
        {"Equipo": "B", "Pts": 4, "PJ": 6},
        {"Equipo": "C", "Pts": 3, "PJ": 4},
    ]
    pic = current_relegation_picture(annual, averages)
    assert set(pic["average_playoff"]) == {"A", "B"}


def test_editorial_story_does_not_pick_goal_difference_in_bottom_points_tie():
    from lpf_competition_narratives import relegation_story

    annual = {
        "A": {"pts": 10, "pj": 20, "dg": -20, "gf": 10},
        "B": {"pts": 10, "pj": 20, "dg": 5, "gf": 30},
        "C": {"pts": 14, "pj": 20, "dg": -30, "gf": 9},
    }
    text = relegation_story(annual, [], annual_relegations=1, average_relegations=0)
    assert "empate en el fondo" in text.lower()
    assert "partido desempate" in text.lower()
    assert "hoy el último es **A**" not in text
    assert "hoy el último es **B**" not in text
