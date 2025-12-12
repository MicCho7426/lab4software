from django.db import models
from datetime import date as _date
from django.utils import timezone
from django.core.exceptions import ValidationError
from .services import DrugInfoService


class Medication(models.Model):
    """
    Represents a prescribed medication with dosage and daily schedule.
    """
    name = models.CharField(max_length=100)
    dosage_mg = models.PositiveIntegerField()
    prescribed_per_day = models.PositiveIntegerField(help_text="Expected number of doses per day")

    def clean(self):
        if self.dosage_mg is not None and self.dosage_mg <= 0:
            raise ValidationError({'dosage_mg': 'Dosage must be positive.'})
        if self.prescribed_per_day is not None and self.prescribed_per_day <= 0:
            raise ValidationError({'prescribed_per_day': 'Prescribed amount must be positive.'})

    def __str__(self):
        return f"{self.name} ({self.dosage_mg}mg)"

    def adherence_rate(self):
        logs = self.doselog_set.all()
        if not logs.exists():
            return 0.0
        taken = logs.filter(was_taken=True).count()
        return round((taken / logs.count()) * 100, 2)

    def expected_doses(self, days: int) -> int:
        if days < 0 or self.prescribed_per_day <= 0:
            raise ValueError("Days and schedule must be positive.")
        return days * self.prescribed_per_day

    def adherence_rate_over_period(self, start_date: _date, end_date: _date) -> float:
        if start_date > end_date:
            raise ValueError("start_date must be before or equal to end_date")

        logs = self.doselog_set.filter(
            taken_at__date__gte=start_date,
            taken_at__date__lte=end_date
        )
        days = (end_date - start_date).days + 1
        expected = self.expected_doses(days)

        if expected == 0:
            return 0.0

        taken = logs.filter(was_taken=True).count()
        adherence = (taken / expected) * 100
        return round(adherence, 2)

    def fetch_external_info(self):
        service = DrugInfoService()
        return service.fetch_external_info(self.name)


class DoseLog(models.Model):
    """
    Records the administration of a medication dose.
    """
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    taken_at = models.DateTimeField()
    was_taken = models.BooleanField(default=True)

    class Meta:
        ordering = ["-taken_at"]

    def clean(self):
        if self.taken_at and self.taken_at > timezone.now():
            raise ValidationError({'taken_at': 'Date cannot be in the future.'})

    def __str__(self):
        status = "Taken" if self.was_taken else "Missed"
        when = timezone.localtime(self.taken_at).strftime("%Y-%m-%d %H:%M")
        return f"{self.medication.name} at {when} - {status}"


class DoctorNote(models.Model):
    """
    Represents a note from a doctor associated with a medication.
    """
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    note = models.TextField()
    created_at = models.DateField()

    def __str__(self):
        return f"Note for {self.medication.name} ({self.created_at})"