from django.utils import timezone

from .models import DoctorNote


def last_notes_for_med(med_id: int, limit: int = 10):
    notes = DoctorNote.objects.filter(medication_id=med_id).order_by("-created_at")
    result = []
    for n in notes[:limit]:
        if n.note is not None:
            result.append(n.note)
    return result


def days_since(date):
    now = timezone.now()
    delta = now.date() - date
    return delta.days
