import logging
from datetime import datetime

import dash
import dash_mantine_components as dmc
import pandas as pd
import pytz
from dash import dcc, html
from dash_iconify import DashIconify

from src.connectors.payments import PaymentService, get_custom_fields
from src.core.dates import get_continuance_date
from src.core.dynamic_fields import CaseDynamicFields
from src.services.billings import BillingsService
from src.services.cases import CasesService, get_many_cases

logger = logging.Logger(__name__)

dash.register_page(
    __name__, order=5, path_template="/manage/payments/<payment_id>"
)


class PaymentsTable:
    def __init__(self):
        pass

    def render_header(self):
        return dmc.Grid(
            [
                dmc.GridCol(
                    dmc.Text(
                        "Billing",
                        c="dark",
                        fw=600,
                    ),
                    span=3,
                ),
                dmc.GridCol(
                    dmc.Text(
                        "Payment",
                        c="dark",
                        fw=600,
                    ),
                    span=3,
                ),
                dmc.GridCol(
                    dmc.Text(
                        "Cases",
                        c="dark",
                        fw=600,
                    ),
                    span=3,
                ),
                dmc.GridCol(
                    dmc.Text(
                        "Actions",
                        c="dark",
                        fw=600,
                    ),
                    span=3,
                ),
            ],
            style={"border-bottom": "1px solid #e1e1e1"},
        )

    def int_to_date(self, timestamp):
        date = datetime.fromtimestamp(timestamp)
        # Convert to Chicago timezone
        date = date.astimezone(pytz.timezone("America/Chicago"))
        return date.strftime("%Y-%m-%d %H:%M:%S")

    def render_billing_info(self, checkout):
        customer_details = checkout.get("customer_details", {})
        if customer_details is None:
            return dmc.Text("No customer details", size="sm")
        address = customer_details.get("address", {})

        address_render = []
        if address is not None:
            if address.get("line1"):
                address_render.append(
                    dmc.Text(f"{address.get('line1')}", size="xs")
                )
            if address.get("line2"):
                address_render.append(
                    dmc.Text(f"{address.get('line2')}", size="xs")
                )
            if (
                address.get("postal_code")
                or address.get("city")
                or address.get("state")
            ):
                address_render.append(
                    dmc.Text(
                        f"{address.get('postal_code', '')}, {address.get('city', '')}, {address.get('state', '')}",
                        size="xs",
                    )
                )

        return dmc.Stack(
            [
                dmc.Group(
                    [
                        dmc.Text(
                            f"{customer_details.get('name')}",
                            size="sm",
                            fw=600,
                            c="dark",
                        ),
                        dmc.Text(
                            get_custom_fields(checkout, "birthdate"),
                            size="sm",
                            fw=600,
                            c="dark",
                        ),
                    ],
                    justify="apart",
                ),
                dmc.Group(
                    [
                        dmc.Text(customer_details.get("email"), size="xs"),
                        dmc.Text(customer_details.get("phone"), size="xs"),
                    ],
                    justify="apart",
                ),
            ]
            + address_render,
            gap="xs",
        )

    def render_checkout_info(self, checkout):
        return dmc.Stack(
            [
                dmc.Group(
                    [
                        dmc.Text("Amount", size="sm", fw=600),
                        dmc.Text(
                            f"{checkout.get('amount_total') / 100} $",
                            size="sm",
                        ),
                    ],
                    justify="apart",
                    gap="xs",
                ),
                dmc.Group(
                    [
                        dmc.Text("Date", size="sm", fw=600),
                        dmc.Text(
                            self.int_to_date(checkout.get("created")),
                            size="sm",
                        ),
                    ],
                    justify="apart",
                    gap="xs",
                ),
                dmc.Group(
                    [
                        dmc.Text("Status", size="sm", fw=600),
                        dmc.Badge(
                            checkout.get("status"),
                            size="sm",
                            color=(
                                "green"
                                if checkout.get("status") == "complete"
                                else "red"
                            ),
                        ),
                    ],
                    justify="apart",
                    gap="xs",
                ),
                dmc.Group(
                    [
                        dmc.Text("Driver Name", size="sm", fw=600),
                        dmc.Text(
                            get_custom_fields(
                                checkout, "nameofdriverifdifferentthanpayment"
                            ),
                            size="sm",
                        ),
                    ],
                    justify="apart",
                    gap="xs",
                ),
                dmc.Group(
                    [
                        dmc.Text("Tickets", size="sm", fw=600),
                        dmc.Text(
                            get_custom_fields(checkout, "tickets"),
                            size="sm",
                        ),
                    ],
                    justify="apart",
                    gap="xs",
                ),
            ],
            gap="xs",
        )

    def render_actions(self, checkout):
        styles_locked = {
            "label": {
                "&[data-checked]": {
                    "&, &:hover": {
                        "backgroundColor": dmc.DEFAULT_THEME["colors"]["dark"][
                            9
                        ],
                        "color": "white",
                    },
                },
            }
        }
        styles_onboarded = {
            "label": {
                "&[data-checked]": {
                    "&, &:hover": {
                        "backgroundColor": dmc.DEFAULT_THEME["colors"][
                            "green"
                        ][9],
                        "color": "white",
                    },
                },
            }
        }

        return dmc.Stack(
            [
                dmc.SegmentedControl(
                    data=[
                        {"label": "Locked", "value": "locked"},
                        {"label": "Onboarded", "value": "onboarded"},
                        {"label": "Invoice", "value": "invoice"},
                        {"label": "Not Done", "value": "not_done"},
                    ],
                    value=checkout.billing.get("status"),
                    id={
                        "type": "case-status-select",
                        "index": checkout.get("id"),
                    },
                    color="dark",
                ),
                dmc.Group(
                    [
                        dmc.Button(
                            "Attach to case",
                            color="dark",
                            size="xs",
                            id={
                                "type": "case-attach-button",
                                "index": checkout.get("id"),
                            },
                            disabled=checkout.billing.get("status")
                            == "locked",
                        ),
                    ]
                ),
                html.Div(
                    id={
                        "type": "case-status-select-output",
                        "index": checkout.get("id"),
                    }
                ),
            ]
        )

    def get_case_information(self, case_id, cases_information):
        if case_id is None or case_id == "":
            return dmc.Text("No case", size="sm")
        city = cases_information.get(case_id, {}).get("city")
        court_date = cases_information.get(case_id, {}).get("court_date")
        court_time = cases_information.get(case_id, {}).get("court_time")

        court_date_dt = pd.to_datetime(court_date)

        color = "gray"

        suggested_motion_for_continuance = None

        if court_date_dt is not None:
            if court_date_dt > pd.to_datetime("today") + pd.Timedelta(
                "30 day"
            ):
                color = "dark"
            elif court_date_dt > pd.to_datetime("today") + pd.Timedelta(
                "7 day"
            ):
                color = "yellow"
                # Same day of the following month
                suggested_motion_for_continuance = get_continuance_date(
                    court_date_dt
                )
            else:
                color = "red"
                suggested_motion_for_continuance = get_continuance_date(
                    court_date_dt
                )
        if suggested_motion_for_continuance is None:
            return dmc.Text(
                f"{city} - Court: {court_date} at {court_time}",
                size="sm",
                c=color,
            )
        else:
            return dmc.Stack(
                [
                    dmc.Text(
                        f"{city} - Court: {court_date} at {court_time}",
                        size="sm",
                        c=color,
                    ),
                    dmc.Text(
                        f"Suggested Continuance: {suggested_motion_for_continuance.strftime('%m/%d/%Y')} at {court_time}",
                        size="sm",
                        c="dark",
                    ),
                ]
            )

    def render_cases(self, checkout, cases_information):
        cases_list = get_custom_fields(checkout, "tickets")
        cases_list_attached = [c.case_id for c in checkout.cases]
        if cases_list is None:
            cases_list = []
        else:
            cases_list = (
                cases_list.replace(" ", "").replace("#", "").split(",")
            )

        cases_list = list(set(cases_list + cases_list_attached))

        if len(cases_list) == 0:
            return dmc.Text("No cases", size="sm")

        return dmc.Stack(
            [
                dmc.Group(
                    [
                        html.A(
                            dmc.Text(
                                (
                                    case
                                    if case not in cases_list_attached
                                    else f"{case} (✅ attached)"
                                ),
                                size="sm",
                                fw=600,
                            ),
                            href=f"/manage/cases/{case}",
                            target="_blank",
                        ),
                        dmc.Text(
                            self.get_case_information(case, cases_information),
                            size="sm",
                            fw=600,
                        ),
                    ]
                )
                for case in cases_list
            ]
        )

    def render_participants(self, checkout):
        return dmc.Stack(
            [
                dmc.Text("Cases", size="sm"),
                dmc.Group(
                    [
                        dmc.Text(
                            size="sm",
                        ),
                    ]
                ),
            ]
        )

    def render_row(self, checkout, cases_information):
        return dmc.Grid(
            [
                dmc.GridCol(
                    self.render_billing_info(checkout),
                    span=3,
                ),
                dmc.GridCol(
                    self.render_checkout_info(checkout),
                    span=3,
                ),
                dmc.GridCol(
                    self.render_cases(checkout, cases_information),
                    span=3,
                ),
                dmc.GridCol(
                    self.render_actions(checkout),
                    span=3,
                ),
            ],
            style={"border-bottom": "1px solid #e1e1e1"},
        )

    def render(self, checkouts, cases_information):
        return dmc.Stack(
            [
                self.render_header(),
            ]
            + [
                self.render_row(checkout, cases_information)
                for checkout in checkouts
            ]
        )


def layout(payment_id, **kwargs):
    payment_service = PaymentService()
    if payment_id is not None and payment_id != "none":
        payment = payment_service.get_item(payment_id)

    else:
        starting_after = kwargs.get("starting_after")
        ending_before = kwargs.get("ending_before")
        checkouts = payment_service.get_last_checkouts(
            starting_after=starting_after,
            ending_before=ending_before,
        )
        first_checkout = payment_service.get_last_checkouts(limit=1)

        cases_service = CasesService()
        billings_service = BillingsService()
        cases_details = []
        retrieved_cases = {}

        for checkout_single in checkouts:
            cases = cases_service.get_items(payment_id=checkout_single.id)
            for case in cases:
                retrieved_cases[case.case_id] = case
            billing = billings_service.get_single_item(checkout_single.id)
            if billing is not None:
                checkout_single["billing"] = billing.model_dump()
            else:
                checkout_single["billing"] = {}
            if len(cases) > 0:
                checkout_single["cases"] = cases
            else:
                checkout_single["cases"] = []

            cases_details += (
                get_custom_fields(checkout_single, "tickets")
                .replace(" ", "")
                .replace("#", "")
                .split(",")
                if get_custom_fields(checkout_single, "tickets") is not None
                else []
            )

        # Split cases into 30 cases per request
        cases_list = []

        # Performance optimization
        cases_details = [
            c for c in cases_details if c not in retrieved_cases.keys()
        ]
        for i in range(0, len(cases_details), 30):
            cases_list += get_many_cases(cases_details[i : i + 30])

        cases_list = cases_list + list(retrieved_cases.values())

        cases_information = {
            case.case_id: CaseDynamicFields().update(case, {})
            for case in cases_list
        }

        payments_table = PaymentsTable()
        if checkouts:
            starting_after_link = checkouts[-1].id
            ending_before_link = checkouts[0].id
        return dmc.Card(
            dmc.Stack(
                [
                    dmc.Group(
                        [
                            dmc.Text("Payments", size="xl"),
                            dmc.Text("Recent Payments", size="sm"),
                        ]
                    ),
                    dmc.Drawer(
                        children=[
                            dmc.Stack(
                                [
                                    dmc.Text("Attach this payment to a case"),
                                    dmc.Text("Select case"),
                                    dcc.Store(
                                        id="case-attach-select-details-store",
                                    ),
                                    dcc.Store(
                                        id="case-attach-select-store",
                                    ),
                                    dmc.MultiSelect(
                                        id="case-attach-select",
                                        searchable=True,
                                        data={
                                            "label": "Loading...",
                                            "value": "loading",
                                        },
                                        clearable=True,
                                    ),
                                    html.Div(
                                        id="case-attach-select-output",
                                    ),
                                    dmc.Button(
                                        "Attach",
                                        color="dark",
                                        id="case-attach-payment-button",
                                    ),
                                    html.Div(
                                        dmc.LoadingOverlay(),
                                        id="case-attach-select-details",
                                    ),
                                ],
                                gap="xs",
                            ),
                        ],
                        id="case-attach-modal",
                        position="right",
                        padding="md",
                        size="55%",
                    ),
                    payments_table.render(checkouts, cases_information),
                    dmc.Group(
                        [
                            html.A(
                                dmc.Button(
                                    "Load previous",
                                    leftSection=DashIconify(
                                        icon="teenyicons:arrow-left-outline"
                                    ),
                                    color="dark",
                                    size="sm",
                                ),
                                hidden=(
                                    True
                                    if ending_before_link
                                    == first_checkout[0].id
                                    else False
                                ),
                                href=f"/manage/payments/none?ending_before={ending_before_link}",
                            ),
                            html.A(
                                dmc.Button(
                                    "Load more",
                                    rightSection=DashIconify(
                                        icon="teenyicons:arrow-right-outline"
                                    ),
                                    color="dark",
                                    size="sm",
                                ),
                                href=f"/manage/payments/none?starting_after={starting_after_link}",
                                hidden=(
                                    True if len(checkouts) < 30 else False
                                ),
                            ),
                        ],
                        justify="left",
                    ),
                ]
            )
        )
