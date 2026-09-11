from datetime import date, time

import pytest

from sales.services import boarding_pass_context, legacy_date
from tests.factories import TicketFactory

pytestmark = pytest.mark.django_db


def test_legacy_date_uses_english_month_abbreviations():
    assert legacy_date(date(2022, 9, 1)) == "01SEP2022"
    assert legacy_date(date(2024, 12, 31)) == "31DEC2024"


def test_boarding_pass_context_formats_ticket_data():
    ticket = TicketFactory(
        ticketid="CB00000001",
        seat="B04",
        buy__client__firstname="Maxime",
        buy__client__lastname="Duprat",
        flight__flightnum="CB2204",
        flight__flightdate=date(2022, 9, 1),
        flight__deptime=time(10),
        flight__airportdep__airportid="CDG",
        flight__airportdep__city="Roissy",
        flight__airportarr__airportid="FCO",
        flight__airportarr__city="Fiumicino",
    )

    assert boarding_pass_context(ticket) == {
        "passenger_name": "MAXIME DUPRAT",
        "seat": "B04",
        "flightnum": "CB2204",
        "dep_code": "CDG",
        "arr_code": "FCO",
        "dep_city": "ROISSY-CDG",
        "arr_city": "FIUMICINO-FCO",
        "flightdate_iso": "2022-09-01",
        "flightdate_legacy": "01SEP2022",
        "deptime": "10:00",
        "ticketid": "CB00000001",
    }
