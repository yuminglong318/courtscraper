import logging

import dash
import pandas as pd
from dash import Input, Output, State, callback, ctx

from src.components.conversation import messaging_template
from src.core.config import get_settings

logger = logging.Logger(__name__)

settings = get_settings()


def handle_modal(prefix):

    @callback(
        Output(f"{prefix}-modal", "opened"),
        Output(f"{prefix}-modal-content", "children"),
        Output(f"{prefix}-memory", "data"),
        State(f"{prefix}-memory", "data"),
        Input(f"{prefix}-data-grid", "selectedRows"),
        Input(f"{prefix}-send-all", "n_clicks"),
        Input(f"{prefix}-response-many", "n_clicks"),
        Input("leads-data", "children"),
        prevent_initial_call=True,
    )
    def open_modal(data, selection, *args, **kwargs):
        triggered_id = ctx.triggered_id if ctx.triggered_id else ""

        if selection and (triggered_id == f"{prefix}-response-many"):
            df = pd.DataFrame(selection)
            data = (
                {"df": df.to_dict("records")}
                if data is None
                else {"df": df.to_dict("records")}
            )
            return True, messaging_template(df, prefix), data

        return dash.no_update, dash.no_update, dash.no_update


for prefix in ["outbound", "monitoring"]:
    handle_modal(prefix)


@callback(
    Output("conversation-modal", "opened"),
    Output("conversation-modal-content", "children"),
    Output("conversation-memory", "data"),
    State("conversation-memory", "data"),
    State("monitoring-data-grid", "selectedRows"),
    Input("monitoring-send-all", "n_clicks"),
    Input("conversation-response-many", "n_clicks"),
    Input("leads-data", "children"),
    prevent_initial_call=True,
)
def open_modal(data, selection, *args, **kwargs):
    triggered_id = ctx.triggered_id if ctx.triggered_id else ""
    if selection and (triggered_id == "conversation-response-many"):
        df = pd.DataFrame(selection)

        data = (
            {"df": df.to_dict("records")}
            if data is None
            else {"df": df.to_dict("records")}
        )
        return (
            True,
            messaging_template(df, prefix="conversation", many_responses=True),
            data,
        )
    return dash.no_update, dash.no_update, dash.no_update


# Unselect all rows
@callback(
    Output("monitoring-data-grid", "selectedRows"),
    Input("conversation-response-unselect-all", "n_clicks"),
    prevent_initial_call=True,
)
def unselect_all_rows(*args, **kwargs):
    return []
