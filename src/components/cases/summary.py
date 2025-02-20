import logging

import dash_mantine_components as dmc
from dash import html

from src.components.cases.status import case_statuses, get_case_status_color
from src.components.groups import create_group_item
from src.core import dynamic_fields
from src.models.cases import Case

logger = logging.Logger(__name__)


def get_case_summary(case: Case):
    charges = []
    if case.charges is not None:
        charges = [
            dmc.Text(
                charge.get("charge_description", ""),
                size="sm",
            )
            for charge in case.charges
        ]

    case_data = dynamic_fields.CaseDynamicFields().update(case, {})

    return dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Text(f"Case#{case.case_id}", fw=500),
                    html.Div(hidden=True, children=case.case_id, id="case-id"),
                    dmc.Badge(
                        (
                            case_statuses.get(case.status, {}).get(
                                "short_description"
                            )
                            if case.status is not None
                            else "Filed"
                        ),
                        color=get_case_status_color(case.status),
                        variant="light",
                        size="sm",
                    ),
                ],
                justify="apart",
                mt="md",
                mb="xs",
            ),
            dmc.Divider(variant="solid", className="mt-2"),
            dmc.Title("→ Case Details", order=5, className="mt-3"),
            create_group_item(
                label="Filing Date",
                value=f"{case.filing_date:%B %d, %Y}",
                icon="radix-icons:calendar",
            ),
            # Court Description
            create_group_item(
                label="Court",
                value=case.court_desc,
                icon="mdi:gavel",
            ),
            create_group_item(
                label="Fine",
                value=(
                    f"$ {case.fine.get('total_amount', 'N/A') if case.fine is not None else 'N/A'}"
                ),
                icon="mdi:cash",
            ),
            create_group_item(
                label="Appearance",
                value=(
                    f"{case_data.get('court_date', 'N/A')} {case_data.get('court_time', 'N/A')}"
                ),
                icon="mdi:calendar-clock",
            ),
            dmc.Divider(variant="solid", className="mt-2"),
            dmc.Title("→ Charges", order=5, className="mt-3"),
            html.Div(charges),
            dmc.Divider(variant="solid", className="mt-2"),
            dmc.Title("→ Defendant", order=5, className="mt-3"),
            create_group_item(
                label="Name",
                value=case.formatted_party_name,
                icon="material-symbols:supervised-user-circle-outline",
            ),
            create_group_item(
                label="Date of Birth",
                value=f"{case.birth_date}",
                icon="ps:birthday",
            ),
            create_group_item(
                label="Address",
                value="",
                icon="material-symbols:location-on-outline",
                # Left align
            ),
            dmc.Text(
                case.formatted_party_address,
                size="sm",
                c="dimmed",
                # Right align
            ),
            create_group_item(
                label="Phone",
                value=case.formatted_telephone,
                icon="material-symbols:phone-android-outline",
            ),
            dmc.Divider(variant="solid", className="mt-2"),
            dmc.Title("→ Judge", order=5, className="mt-3"),
            create_group_item(
                label="Name",
                value=(
                    case.judge.get("formatted_name", "")
                    if case.judge is not None
                    else ""
                ),
                icon="fluent-emoji-high-contrast:man-judge",
            ),
            dmc.Divider(variant="solid", className="mt-2"),
            dmc.Title("→ Parties", order=5, className="mt-3"),
            (
                html.Div(
                    [
                        html.Div(
                            [
                                dmc.Title(party.get("desc", ""), order=6),
                                create_group_item(
                                    label="Name",
                                    value=party.get("formatted_partyname", ""),
                                    icon="material-symbols:supervised-user-circle-outline",
                                ),
                                create_group_item(
                                    label="Phone",
                                    value=party.get("formatted_telephone", ""),
                                    icon="material-symbols:phone-android-outline",
                                ),
                                create_group_item(
                                    label="Address",
                                    value="",
                                    icon="material-symbols:location-on-outline",
                                ),
                                dmc.Text(
                                    party.get("formatted_partyaddress", ""),
                                    size="sm",
                                    c="dimmed",
                                    # Right align
                                ),
                            ]
                        )
                        for party in case.parties
                    ]
                )
                if case.parties is not None
                else ""
            ),
        ],
        gap="0px",
    )
