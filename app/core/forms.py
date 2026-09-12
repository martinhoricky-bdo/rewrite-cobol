from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.forms.renderers import TemplatesSetting


class FilterForm(forms.Form):
    """Provide validation helpers shared by filter forms."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required = [name for name, field in self.fields.items() if field.required]
        if required:
            raise ImproperlyConfigured(f"Filter fields must not be required: {', '.join(required)}")

    def value(self, name: str, default=None):
        if not self.is_bound:
            return default
        errors = self.errors
        value = self.cleaned_data.get(name)
        return default if name in errors or value in self.fields[name].empty_values else value

    def is_empty(self) -> bool:
        return not any(
            self[name].value() not in field.empty_values for name, field in self.fields.items()
        )


class FormRenderer(TemplatesSetting):
    """Render bound fields with the application's shared field template."""

    field_template_name = "core/forms/field.html"
