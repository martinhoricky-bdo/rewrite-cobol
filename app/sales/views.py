"""Sales views reconstruct SRCHFLY, SRCHTKT, PRINTCI, SELLCOB1, missing SELLCOB2, and
PRINTPA workflows.
"""

from decimal import DecimalException

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.views.generic import CreateView, DetailView, FormView, UpdateView

from accounts.permissions import RoleRequiredMixin, check_role, role_required
from accounts.roles import Role
from core.exceptions import NotFound
from core.messages import E_FLT_03, E_SEL_05_ID, E_SEL_09, E_TKT_02, E_TKT_03
from core.views import generic
from operations.models import Flight
from operations.services import search_flights

from .forms import (
    FlightSearchForm,
    PassengerFilterForm,
    PassengerForm,
    SellStep1Form,
    SellStep2Form,
    TicketSearchForm,
)
from .models import Buy, Passenger, Ticket
from .services import (
    SESSION_KEY,
    SaleError,
    SaleQuote,
    boarding_pass_context,
    confirm_sale,
    duplicate_email_warning,
    quote_sale,
    search_tickets,
)


class SalesView(RoleRequiredMixin):
    """Provide SalesView behavior for the sales legacy programs and UC-S01 through UC-S09."""

    allowed_roles = (Role.SALES,)


class SalesAndCeoView(RoleRequiredMixin):
    """Provide SalesAndCeoView behavior for the sales legacy programs and UC-S01 through
    UC-S09.
    """

    allowed_roles = (Role.SALES, Role.CEO)


class SaleSessionMixin:
    """Provide SaleSessionMixin behavior for the sales legacy programs and UC-S01 through
    UC-S09.
    """

    def get_quote(self):
        """Implement get_quote behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
        data = self.request.session.get(SESSION_KEY)
        if data is None:
            return None
        try:
            return SaleQuote.from_session(data)
        except (DecimalException, KeyError, TypeError, ValueError):
            self.clear_quote()
            return None

    def store_quote(self, quote):
        """Implement store_quote behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
        self.request.session[SESSION_KEY] = quote.to_session()

    def clear_quote(self):
        """Implement clear_quote behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
        self.request.session.pop(SESSION_KEY, None)


class SellStep1View(SalesView, SaleSessionMixin, generic.FormErrorsAsMessagesMixin, FormView):
    """Reconstruct SELLCOB1 (SELL1-COB), map SELLMS/SELLMP, and ordered E-SEL-01 through
    E-SEL-08 checks for UC-S06.
    """

    form_class = SellStep1Form
    template_name = "sales/sell_step1.html"

    def get_initial(self):
        """Implement get_initial behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
        return {
            "clientid": self.request.GET.get("clientid", ""),
            "flightnum": self.request.GET.get("flightnum", ""),
            "flightdate": self.request.GET.get("date", ""),
        }

    def get_context_data(self, **kwargs):
        """Implement get_context_data behavior for the sales legacy programs and UC-S01
        through UC-S09.
        """
        kwargs.setdefault("quote", self.get_quote())
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        """Implement form_valid behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
        try:
            quote = quote_sale(**form.cleaned_data, today=timezone.localdate())
        except SaleError as exc:
            self.clear_quote()
            messages.error(self.request, exc.message)
            return self.form_invalid(form)
        self.store_quote(quote)
        return self.render_to_response(self.get_context_data(form=form, quote=quote))

    def form_invalid(self, form):
        """Implement form_invalid behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
        self.clear_quote()
        return super().form_invalid(form)


class SellStep2View(SalesView, SaleSessionMixin, FormView):
    """Reconstruct missing SELLCOB2 from SELL2-MAP and screenshots for UC-S07."""

    form_class = SellStep2Form
    template_name = "sales/sell_step2.html"

    def dispatch(self, request, *args, **kwargs):
        """Implement dispatch behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
        if response := check_role(request, self.allowed_roles):
            return response
        self.quote = self.get_quote()
        if self.quote is None:
            messages.error(request, E_SEL_09)
            return redirect("sales:sell_step1")
        if request.method == "POST" and request.POST.get("action") == "return":
            return redirect("sales:sell_step1")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Implement get_form_kwargs behavior for the sales legacy programs and UC-S01
        through UC-S09.
        """
        kwargs = super().get_form_kwargs()
        kwargs["count"] = self.quote.count
        return kwargs

    def get_initial(self):
        """Implement get_initial behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
        return {"client_1": self.quote.client_id}

    def get_context_data(self, **kwargs):
        """Implement get_context_data behavior for the sales legacy programs and UC-S01
        through UC-S09.
        """
        form = kwargs.pop("form", None) or self.get_form()
        names = kwargs.pop(
            "names", {1: self.quote.client_name} if self.request.method == "GET" else {}
        )
        return super().get_context_data(
            quote=self.quote, rows=form.rows(names), form=form, **kwargs
        )

    def form_valid(self, form):
        """Implement form_valid behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
        client_ids = [
            form.cleaned_data[f"client_{number}"] for number in range(1, self.quote.count + 1)
        ]
        if self.request.POST.get("action") == "confirm":
            try:
                buy = confirm_sale(
                    quote=self.quote,
                    client_ids=client_ids,
                    seller=self.request.user.employee,
                    now=timezone.localtime(),
                )
            except SaleError as exc:
                messages.error(self.request, exc.message)
            else:
                self.clear_quote()
                return redirect("sales:buy_detail", buyid=buy.pk)
        names = {}
        for number, client_id in enumerate(client_ids, start=1):
            passenger = Passenger.objects.filter(pk=client_id).first()
            names[number] = passenger.full_name if passenger else E_SEL_05_ID.format(id=client_id)
        return self.render_to_response(self.get_context_data(form=form, names=names))


@role_required(Role.SALES)
def passenger_name(request):
    """Implement passenger_name behavior for the sales legacy programs and UC-S01 through
    UC-S09.
    """
    raw_client_id = request.GET.get("clientid")
    if raw_client_id is None:
        raw_client_id = next(
            (value for key, value in request.GET.items() if key.startswith("client_")), ""
        )
    try:
        client_id = int(raw_client_id)
    except ValueError:
        client_id = 0
    passenger = Passenger.objects.filter(pk=client_id).first()
    if passenger:
        return HttpResponse(format_html('<span class="name">{}</span>', passenger.full_name))
    return HttpResponse(
        format_html('<span class="error">{}</span>', E_SEL_05_ID.format(id=client_id))
    )


class PassengerView(SalesView):
    """Design: implement UC-S04 and UC-S05, replacing the unimplemented F7 PASS REG.
    function.
    """

    model = Passenger
    pk_url_kwarg = "clientid"
    cancel_url_name = "sales:passenger_list"


class PassengerListView(PassengerView, generic.PageTitleMixin, generic.FilteredListView):
    """Design: implement UC-S04 and UC-S05, replacing the unimplemented F7 PASS REG.
    function.
    """

    page_title = "Passengers"
    template_name = "sales/passenger_list.html"
    filter_form_class = PassengerFilterForm
    paginate_by = 10

    def filter_queryset(self, queryset, form):
        """Implement filter_queryset behavior for the sales legacy programs and UC-S01
        through UC-S09.
        """
        return queryset.filter_by(**form.cleaned_data) if form.is_valid() else queryset.none()


class PassengerDetailView(PassengerView, generic.PageTitleMixin, DetailView):
    """Design: implement UC-S04 and UC-S05, replacing the unimplemented F7 PASS REG.
    function.
    """

    template_name = "sales/passenger_detail.html"
    context_object_name = "passenger"

    def get_page_title(self):
        """Implement get_page_title behavior for the sales legacy programs and UC-S01
        through UC-S09.
        """
        return f"Passenger {self.object.pk}"

    def get_context_data(self, **kwargs):
        """Implement get_context_data behavior for the sales legacy programs and UC-S01
        through UC-S09.
        """
        tickets = Ticket.objects.with_related().for_passenger(self.object)
        return super().get_context_data(tickets=tickets, **kwargs)


class PassengerFormView(
    PassengerView, generic.PageTitleMixin, generic.CancelUrlMixin, generic.SavedMessageMixin
):
    """Design: implement UC-S04 and UC-S05, replacing the unimplemented F7 PASS REG.
    function.
    """

    template_name = "core/form.html"
    model_label = "Passenger"

    def get_cancel_url(self):
        """Implement get_cancel_url behavior for the sales legacy programs and UC-S01
        through UC-S09.
        """
        if self.object:
            return reverse("sales:passenger_detail", kwargs={"clientid": self.object.pk})
        return super().get_cancel_url()

    def get_page_title(self):
        """Implement get_page_title behavior for the sales legacy programs and UC-S01
        through UC-S09.
        """
        return f"Edit passenger {self.object.pk}" if self.object else "New passenger"

    def form_valid(self, form):
        """Implement form_valid behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
        warning = duplicate_email_warning(
            form.cleaned_data["email"], getattr(self.object, "pk", None)
        )
        if warning:
            messages.warning(self.request, warning)
        return super().form_valid(form)


class PassengerCreateView(PassengerFormView, CreateView):
    """Design: implement UC-S04 and UC-S05, replacing the unimplemented F7 PASS REG.
    function.
    """

    form_class = PassengerForm


class PassengerUpdateView(PassengerFormView, UpdateView):
    """Design: implement UC-S04 and UC-S05, replacing the unimplemented F7 PASS REG.
    function.
    """

    form_class = PassengerForm


class FlightSearchView(RoleRequiredMixin, generic.SearchListView):
    """Reconstruct SRCHFLY (CICS/SALES-MAP/SRCHFLY-COB), map SRCHFLI/SRCHPA, for UC-S01."""

    allowed_roles = (Role.SALES, Role.CEO, Role.SCHEDULE, Role.CREW)
    model = Flight
    template_name = "sales/flight_search.html"
    filter_form_class = FlightSearchForm
    empty_message = E_FLT_03
    paginate_by = 10

    def search_queryset(self, form):
        """Implement search_queryset behavior for the sales legacy programs and UC-S01
        through UC-S09.
        """
        return search_flights(**form.cleaned_data, today=timezone.localdate())


class TicketSearchView(SalesAndCeoView, generic.SearchListView):
    """Reconstruct SRCHTKT (SRCHTKT-COB), map SRCHTKT/SRCHTK, for UC-S02 using a list
    instead of one-ticket paging.
    """

    model = Ticket
    template_name = "sales/ticket_search.html"
    filter_form_class = TicketSearchForm
    empty_message = E_TKT_02
    paginate_by = 10

    def search_queryset(self, form):
        """Implement search_queryset behavior for the sales legacy programs and UC-S01
        through UC-S09.
        """
        return search_tickets(**form.cleaned_data)


class TicketView(SalesAndCeoView, DetailView):
    """Provide TicketView behavior for the sales legacy programs and UC-S01 through UC-S09."""

    model = Ticket
    pk_url_kwarg = "ticketid"

    def get_object(self, queryset=None):
        """Implement get_object behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
        ticket = (
            Ticket.objects.with_related().filter(ticketid=self.kwargs["ticketid"].upper()).first()
        )
        if ticket is None:
            raise NotFound(E_TKT_03)
        return ticket


class TicketDetailView(TicketView):
    """Reconstruct PRINTCI (PRINT-TICKET-COB), pattern TICKET-FORMAT, for UC-S03."""

    template_name = "sales/ticket_detail.html"


class BoardingPassView(TicketView):
    """Render the PRINTCI boarding pass from PRINT-TICKET-COB and TICKET-FORMAT for UC-S03."""

    template_name = "sales/boarding_pass.html"

    def get_context_data(self, **kwargs):
        """Implement get_context_data behavior for the sales legacy programs and UC-S01
        through UC-S09.
        """
        return super().get_context_data(
            boarding_pass=boarding_pass_context(self.object),
            ticketid=self.object.ticketid,
            **kwargs,
        )


class BuyView(SalesAndCeoView, DetailView):
    """Provide BuyView behavior for the sales legacy programs and UC-S01 through UC-S09."""

    model = Buy
    pk_url_kwarg = "buyid"

    def get_queryset(self):
        """Implement get_queryset behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
        return Buy.objects.with_related()


class BuyDetailView(BuyView):
    """Reconstruct PRINTPA (RECEIPT-COB), pattern RECEIPT-FORMAT, for UC-S08 without
    payment-method storage.
    """

    template_name = "sales/buy_detail.html"


class ReceiptView(BuyView):
    """Reconstruct PRINTPA (RECEIPT-COB), pattern RECEIPT-FORMAT, for UC-S09 without
    payment-method storage.
    """

    template_name = "sales/receipt.html"


class BoardingPassesView(BuyView):
    """Render multiple PRINTCI boarding passes from TICKET-FORMAT for UC-S03."""

    template_name = "sales/boarding_passes.html"

    def get_context_data(self, **kwargs):
        """Implement get_context_data behavior for the sales legacy programs and UC-S01
        through UC-S09.
        """
        tickets = Ticket.objects.with_related().for_buy(self.object)
        passes = [boarding_pass_context(ticket) for ticket in tickets]
        return super().get_context_data(boarding_passes=passes, **kwargs)
