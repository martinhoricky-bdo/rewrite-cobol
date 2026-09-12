"""Design: reusable generic views replace repeated web CRUD mechanics rather than a
specific legacy program.
"""

from typing import Any

from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.forms import BaseForm
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DeleteView, ListView

from accounts.permissions import current_role
from core.messages import E_REF_01


class PageTitleMixin:
    """Add a configurable page title to the template context."""

    page_title: str = ""

    def get_page_title(self) -> str:
        """Implement get_page_title behavior for the shared CICS-inspired application
        design.
        """
        return self.page_title

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Implement get_context_data behavior for the shared CICS-inspired application
        design.
        """
        return super().get_context_data(page_title=self.get_page_title(), **kwargs)


class CancelUrlMixin:
    """Add an optional reversed cancellation URL to the template context."""

    cancel_url_name: str | None = None

    def get_cancel_url(self) -> str | None:
        """Implement get_cancel_url behavior for the shared CICS-inspired application
        design.
        """
        return reverse(self.cancel_url_name) if self.cancel_url_name else None

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Implement get_context_data behavior for the shared CICS-inspired application
        design.
        """
        return super().get_context_data(cancel_url=self.get_cancel_url(), **kwargs)


class EditableByMixin:
    """Expose whether the current user's role permits editing the object."""

    edit_roles = ()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Implement get_context_data behavior for the shared CICS-inspired application
        design.
        """
        can_edit = current_role(self.request.user) in self.edit_roles
        return super().get_context_data(can_edit=can_edit, **kwargs)


class SavedMessageMixin:
    """Show a success message after a model form is saved."""

    saved_message = "{model} {pk} saved."
    model_label: str | None = None

    def get_saved_message(self) -> str:
        """Implement get_saved_message behavior for the shared CICS-inspired application
        design.
        """
        model = self.model_label or self.object._meta.verbose_name.capitalize()
        return self.saved_message.format(model=model, pk=self.object.pk)

    def form_valid(self, form: BaseForm) -> HttpResponse:
        """Implement form_valid behavior for the shared CICS-inspired application design."""
        response = super().form_valid(form)
        messages.success(self.request, self.get_saved_message())
        return response


class FormErrorsAsMessagesMixin:
    """Copy all form validation errors into Django messages."""

    def form_invalid(self, form: BaseForm) -> HttpResponse:
        """Implement form_invalid behavior for the shared CICS-inspired application design."""
        form_errors_as_messages(self.request, form)
        return super().form_invalid(form)


def form_errors_as_messages(request, form: BaseForm) -> None:
    """Copy every form validation error to the request message storage."""
    for field in form:
        for error in field.errors:
            messages.error(request, error)
    for error in form.non_field_errors():
        messages.error(request, error)


class FilteredListView(ListView):
    """Build and expose a form that filters a list queryset."""

    filter_form_class = None

    def get_filter_form(self) -> BaseForm | None:
        """Implement get_filter_form behavior for the shared CICS-inspired application
        design.
        """
        if self.filter_form_class is None:
            return None
        return self.filter_form_class(self.request.GET)

    def filter_queryset(self, queryset, form: BaseForm | None):
        """Implement filter_queryset behavior for the shared CICS-inspired application
        design.
        """
        return queryset

    def get_queryset(self):
        """Implement get_queryset behavior for the shared CICS-inspired application design."""
        self.filter_form = self.get_filter_form()
        return self.filter_queryset(super().get_queryset(), self.filter_form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Implement get_context_data behavior for the shared CICS-inspired application
        design.
        """
        return super().get_context_data(form=self.filter_form, **kwargs)

    def paginate_queryset(self, queryset, page_size: int):
        """Implement paginate_queryset behavior for the shared CICS-inspired application
        design.
        """
        paginator = self.get_paginator(queryset, page_size)
        page = paginator.get_page(self.request.GET.get(self.page_kwarg))
        return paginator, page, page.object_list, page.has_other_pages()


class SearchListView(FormErrorsAsMessagesMixin, FilteredListView):
    """Display search results only after a valid bound search form."""

    empty_message = "No results found."

    def get_filter_form(self) -> BaseForm:
        """Implement get_filter_form behavior for the shared CICS-inspired application
        design.
        """
        return self.filter_form_class(self.request.GET or None)

    def search_queryset(self, form: BaseForm):
        """Implement search_queryset behavior for the shared CICS-inspired application
        design.
        """
        return self.model._default_manager.all()

    def filter_queryset(self, queryset, form: BaseForm):
        """Implement filter_queryset behavior for the shared CICS-inspired application
        design.
        """
        if not form.is_bound:
            return queryset.none()
        if not form.is_valid():
            self.form_invalid(form)
            return queryset.none()
        results = self.search_queryset(form)
        if not results.exists():
            messages.info(self.request, self.empty_message)
        return results

    def form_invalid(self, form: BaseForm) -> None:
        """Implement form_invalid behavior for the shared CICS-inspired application design."""
        form_errors_as_messages(self.request, form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Implement get_context_data behavior for the shared CICS-inspired application
        design.
        """
        context = super().get_context_data(**kwargs)
        if not self.filter_form.is_bound or not self.filter_form.is_valid():
            context.update(page_obj=None, is_paginated=False)
        return context


class ProtectedDeleteView(PageTitleMixin, DeleteView):
    """Delete an object while converting protected references into a message."""

    template_name = "core/confirm_delete.html"
    deleted_message = "{model} {pk} deleted."
    model_label: str | None = None

    def _model_label(self) -> str:
        return self.model_label or self.object._meta.verbose_name.capitalize()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Implement get_context_data behavior for the shared CICS-inspired application
        design.
        """
        return super().get_context_data(object_label=self.object._meta.verbose_name, **kwargs)

    def form_valid(self, form: BaseForm) -> HttpResponse:
        """Implement form_valid behavior for the shared CICS-inspired application design."""
        pk = self.object.pk
        try:
            self.object.delete()
        except ProtectedError as error:
            protected = list(error.protected_objects)
            unique = {(item._meta.label, item.pk) for item in protected}
            related = protected[0]._meta.verbose_name_plural if protected else "objects"
            messages.error(
                self.request,
                E_REF_01.format(Entity=self._model_label(), n=len(unique), related=related),
            )
        else:
            messages.success(
                self.request, self.deleted_message.format(model=self._model_label(), pk=pk)
            )
        return redirect(self.get_success_url())
