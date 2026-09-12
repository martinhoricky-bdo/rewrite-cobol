import re
from datetime import date, timedelta
from time import time_ns
from urllib.parse import urlencode

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def _sold_cb1104_dates(page: Page, base_url: str, client_id: int) -> set[str]:
    """Read dates already booked by a passenger using only the public UI."""
    page.goto(f"{base_url}/sales/tickets/?{urlencode({'clientid': client_id})}")
    dates: set[str] = set()
    while True:
        for row in page.locator("tbody tr").all():
            cells = row.locator("td")
            if cells.count() >= 5 and cells.nth(3).inner_text().strip() == "CB1104":
                dates.add(cells.nth(4).inner_text().strip())
        next_link = page.get_by_role("link", name="Next")
        if next_link.count() == 0:
            return dates
        next_link.click()


def _available_sale_date(page: Page, base_url: str) -> str:
    booked = _sold_cb1104_dates(page, base_url, 641)
    booked.update(_sold_cb1104_dates(page, base_url, 100))
    today = date.today()
    candidates = [today + timedelta(days=7)]
    candidates.extend(today + timedelta(days=offset) for offset in range(1, 15) if offset != 7)
    for candidate in candidates:
        value = candidate.isoformat()
        if value in booked:
            continue
        page.goto(
            f"{base_url}/sales/flights/?{urlencode({'flightnum': 'CB1104', 'flightdate': value})}"
        )
        if page.locator("tbody tr", has_text="CB1104").count():
            return value
    pytest.fail("No unbooked CB1104 flight for passengers 641 and 100 in the next 14 days")


def test_complete_sale_ticket_search_and_boarding_pass(sales_page: Page, base_url: str) -> None:
    flight_date = _available_sale_date(sales_page, base_url)
    row = sales_page.locator("tbody tr", has_text="CB1104").filter(has_text=flight_date)
    row.get_by_role("link", name="Sell").click()
    expect(sales_page.get_by_label("FLIGHT NUM")).to_have_value("CB1104")
    expect(sales_page.get_by_label("DATE")).to_have_value(flight_date)
    sales_page.get_by_label("CLIENT ID").fill("641")
    sales_page.get_by_label("PASS NUMBER").fill("2")
    sales_page.get_by_role("button", name="Research").click()
    expect(sales_page.get_by_text("241.98 EUR", exact=True)).to_be_visible()
    sales_page.get_by_role("button", name="Insert passengers").click()
    passenger_fields = sales_page.get_by_label("CLIENTID")
    expect(passenger_fields.nth(0)).to_have_value("641")
    passenger_fields.nth(1).fill("100")
    sales_page.get_by_role("button", name="Check names").click()
    expect(sales_page.get_by_text("RAFAEL HILLETT", exact=True)).to_be_visible()
    sales_page.get_by_role("button", name="Confirm passengers").click()
    expect(
        sales_page.get_by_role("heading", name=re.compile(r"Sale \d+ completed\."))
    ).to_be_visible()
    ticket_rows = sales_page.locator("tbody tr")
    expect(ticket_rows).to_have_count(2)
    rafael_row = ticket_rows.filter(has_text="RAFAEL HILLETT")
    ticket_id = rafael_row.locator("td").nth(0).inner_text().strip()
    seat = rafael_row.locator("td").nth(2).inner_text().strip()
    sales_page.get_by_role("button", name="Print receipt").click()
    expect(sales_page.get_by_text("MONTANT = 241.98 EUR", exact=True)).to_be_visible()
    sales_page.get_by_role("link", name="Back").click()
    expect(
        sales_page.get_by_role("heading", name=re.compile(r"Sale \d+ completed\."))
    ).to_be_visible()
    sales_page.get_by_role("link", name="Search ticket").click()
    sales_page.get_by_label("TICKET ID").fill(ticket_id)
    sales_page.get_by_role("button", name="Search").click()
    sales_page.get_by_role("link", name=ticket_id).click()
    with sales_page.expect_popup() as boarding_info:
        sales_page.get_by_role("button", name="Print boarding pass").click()
    boarding_pass = boarding_info.value
    # The name and seat appear on the main pass and on the detachable stub.
    expect(boarding_pass.get_by_text("RAFAEL HILLETT", exact=True).first).to_be_visible()
    expect(boarding_pass.get_by_text(seat, exact=True).first).to_be_visible()


def test_create_and_edit_passenger(sales_page: Page) -> None:
    unique = str(time_ns())
    sales_page.get_by_role("link", name="Passengers").click()
    sales_page.get_by_role("button", name="New passenger").click()
    values = {
        "FIRSTNAME": "PLAYWRIGHT",
        "LASTNAME": f"E2E-{unique}"[-30:],
        "ADDRESS": "12 Browser Street",
        "CITY": "PARIS",
        "COUNTRY": "FRANCE",
        "ZIPCODE": "75001",
        "TELEPHONE": "+33 1 23 45 67",
        "EMAIL": f"e2e-{unique}@example.test",
    }
    for label, value in values.items():
        sales_page.get_by_label(label).fill(value)
    sales_page.get_by_role("button", name="Save").click()
    expect(sales_page.get_by_text(values["LASTNAME"], exact=True)).to_be_visible()
    sales_page.get_by_role("button", name="Edit", exact=True).click()
    sales_page.get_by_label("CITY").fill("LYON")
    sales_page.get_by_role("button", name="Save").click()
    expect(sales_page.get_by_text("LYON", exact=True)).to_be_visible()
