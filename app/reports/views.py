"""Design: report views implement crew shifts in UC-C01 and CEO summaries in UC-E01."""

from django.utils import timezone
from django.views.generic import TemplateView

from accounts.permissions import RoleRequiredMixin
from accounts.roles import Role
from core.views import generic

from .forms import PeriodFilterForm, ShiftPeriodFilterForm
from .services import crew_shifts, dashboard_report


class MyShiftsView(RoleRequiredMixin, generic.PageTitleMixin, generic.FilteredListView):
    """Provide MyShiftsView behavior for Design use cases UC-C01 and UC-E01."""

    allowed_roles = (Role.CREW,)
    page_title = "My shifts"
    template_name = "reports/my_shifts.html"
    filter_form_class = ShiftPeriodFilterForm
    paginate_by = 20

    def get_queryset(self):
        """Implement get_queryset behavior for Design use cases UC-C01 and UC-E01."""
        self.filter_form = self.get_filter_form()
        include_past = self.filter_form.value("past", False)
        return crew_shifts(
            self.request.user.employee,
            today=timezone.localdate(),
            include_past=include_past,
        )

    def get_context_data(self, **kwargs):
        """Implement get_context_data behavior for Design use cases UC-C01 and UC-E01."""
        return super().get_context_data(
            include_past=self.filter_form.value("past", False), **kwargs
        )


class DashboardView(RoleRequiredMixin, TemplateView):
    """Provide DashboardView behavior for Design use cases UC-C01 and UC-E01."""

    allowed_roles = (Role.CEO,)
    template_name = "reports/dashboard.html"

    def get_context_data(self, **kwargs):
        """Implement get_context_data behavior for Design use cases UC-C01 and UC-E01."""
        today = timezone.localdate()
        first_day = today.replace(day=1)
        form = PeriodFilterForm(self.request.GET)
        date_from = form.value("from", first_day)
        date_to = form.value("to", today)
        if date_from > date_to:
            date_from = first_day
            date_to = today
        shown = PeriodFilterForm({"from": date_from.isoformat(), "to": date_to.isoformat()})
        return super().get_context_data(
            form=shown,
            date_from=date_from,
            date_to=date_to,
            **dashboard_report(date_from, date_to),
            **kwargs,
        )
