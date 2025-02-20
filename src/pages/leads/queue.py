import logging

import dash
import dash_mantine_components as dmc
from dash import html

from src.components.filters import get_court_selector
from src.components.inputs import generate_form_group

logger = logging.Logger(__name__)

dash.register_page(__name__, class_icon="ti ti-file", order=1)


def layout():
    return html.Div(
        [
            dmc.Group(
                [
                    get_court_selector(),
                    generate_form_group(
                        label="Status",
                        id="leads-status",
                        placeholder="Select a Status",
                        type="Dropdown",
                        options=[
                            "contacted",
                            "not_contacted",
                            "won",
                            "lost",
                            "wait",
                        ],
                        value="contacted",
                        persistence_type="session",
                        persistence=True,
                    ),
                ],
                justify="center",
                grow=True,
            ),
            html.Div(
                id="leads-queue-phone-update",
                style={"display": "none"},
            ),
            html.Div(
                id="leads-queue-refresh",
                style={"display": "none"},
            ),
            dmc.Grid(
                id="leads-queue-grid",
                className="mt-1",
                justify="center",
                align="stretch",
            ),
        ]
    )
