from app import create_app


def test_dash_preloads_split_stylesheets_for_the_first_render():
    app = create_app()

    css_resources = app.css.get_all_css()
    asset_paths = [resource.get("asset_path") for resource in css_resources]

    assert "10-base.css" in asset_paths
    assert "20-layout.css" in asset_paths
    assert "30-sidebar.css" in asset_paths
    assert "40-dashboard-features.css" in asset_paths
    assert "90-responsive.css" in asset_paths

    html = app.index()

    assert "/assets/10-base.css" in html
    assert "/assets/20-layout.css" in html
    assert "/assets/30-sidebar.css" in html
    assert "/assets/40-dashboard-features.css" in html
    assert "/assets/90-responsive.css" in html
