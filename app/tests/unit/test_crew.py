import pytest
from django.core.exceptions import ValidationError

from tests.factories import CrewFactory

pytestmark = pytest.mark.django_db


def test_crew_rejects_duplicate_members():
    crew = CrewFactory.build()
    crew.copilote = crew.commander
    with pytest.raises(ValidationError, match="Crew members must be unique"):
        crew.clean()
