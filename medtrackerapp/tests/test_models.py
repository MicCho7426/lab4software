from django.test import TestCase
from medtrackerapp.models import Medication, DoseLog
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from datetime import date as _date


class MedicationModelTests(TestCase):

    def test_str_returns_name_and_dosage(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.assertEqual(str(med), "Aspirin (100mg)")

    def test_adherence_rate_all_doses_taken(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        now = timezone.now()

        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=30))
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=1))

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 100.0)

    def test_adherence_rate_half_doses_taken(self):
        med = Medication.objects.create(name="MidDrug", dosage_mg=50, prescribed_per_day=2)
        now = timezone.now()

        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=1))
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=2), was_taken=False)

        adherence = med.adherence_rate()
        self.assertAlmostEqual(adherence, 50.0, places=2)

    def test_invalid_dosage_raises_error(self):
        med_zero = Medication(name="ZeroDose", dosage_mg=0, prescribed_per_day=1)

        with self.assertRaises(ValidationError) as cm:
            med_zero.full_clean()
        self.assertIn('dosage_mg', cm.exception.message_dict)

    def test_adherence_rate_over_period_valid(self):
        med = Medication.objects.create(name="DailyPill", dosage_mg=10, prescribed_per_day=1)

        start = _date(2025, 11, 25)
        end = _date(2025, 11, 27)

        DoseLog.objects.create(medication=med, taken_at=timezone.make_aware(timezone.datetime(2025, 11, 25, 8, 0)))
        DoseLog.objects.create(medication=med, taken_at=timezone.make_aware(timezone.datetime(2025, 11, 26, 8, 0)))
        DoseLog.objects.create(
            medication=med,
            taken_at=timezone.make_aware(timezone.datetime(2025, 11, 27, 8, 0)),
            was_taken=False
        )

        adherence = med.adherence_rate_over_period(start, end)
        self.assertAlmostEqual(adherence, 66.67, places=2)


class DoseLogModelTests(TestCase):

    def setUp(self):
        self.medication = Medication.objects.create(name="TestMed", dosage_mg=10, prescribed_per_day=1)

    def test_dose_log_date_in_future_raises_error(self):
        future_time = timezone.now() + timedelta(minutes=5)
        dose = DoseLog(medication=self.medication, taken_at=future_time)

        with self.assertRaises(ValidationError) as cm:
            dose.full_clean()

        self.assertIn('taken_at', cm.exception.message_dict)
