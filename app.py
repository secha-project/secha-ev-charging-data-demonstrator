from dash import Dash

from dashboard.callbacks import register_callbacks
from dashboard.layout import create_layout


def create_app() -> Dash:
    app = Dash(__name__)
    app.title = "EV Charging Demonstrator"
    app.layout = create_layout()
    register_callbacks(app)
    # Preload Dash assets so the first rendered page includes the CSS bundle.
    app._setup_server()
    return app


app = create_app()
server = app.server


if __name__ == "__main__":
    app.run(debug=True)
