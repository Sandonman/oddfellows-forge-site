from cc_v3.builder_tab import format_builder_summary
from cc_v3.leveling import build_level_snapshot


def test_builder_summary_includes_gained_and_visible_features_without_lookahead():
    snap = build_level_snapshot("Fighter", 3, look_ahead=False)
    text = format_builder_summary(snap, look_ahead=False)

    assert "Gained at this level:" in text
    assert "Visible features:" in text
    for feature in snap.gained_features:
        assert f"- {feature}" in text


def test_builder_summary_shows_future_feature_tags_with_lookahead():
    snap = build_level_snapshot("Fighter", 3, look_ahead=True)
    text = format_builder_summary(snap, look_ahead=True)

    assert "Look Ahead: On" in text
    assert any(line.startswith("- L20:") for line in text.splitlines())
