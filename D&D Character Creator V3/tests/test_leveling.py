from cc_v3.leveling import MAX_LEVEL, build_level_snapshot, level_up


def test_build_level_snapshot_without_lookahead_shows_current_features_only():
    snap = build_level_snapshot("Fighter", 3, look_ahead=False)
    assert snap.level == 3
    assert snap.gained_features
    assert snap.visible_features == snap.gained_features


def test_build_level_snapshot_with_lookahead_includes_future_features():
    snap = build_level_snapshot("Fighter", 3, look_ahead=True)
    assert any(item.startswith("L3:") for item in snap.visible_features)
    assert any(item.startswith("L20:") for item in snap.visible_features)


def test_level_up_advances_level_and_respects_max_level():
    snap = level_up("Wizard", 1)
    assert snap.level == 2

    try:
        level_up("Wizard", MAX_LEVEL)
        assert False, "expected ValueError at max level"
    except ValueError:
        pass
