from rest_framework.test import APITestCase
from medtrackerapp.models import Medication, DoseLog
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from datetime import date, timedelta
from django.utils import timezone
from django.db import IntegrityError


class MedicationViewTests(APITestCase):

    def setUp(self):
        self.med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.list_url = reverse("medication-list")
        self.detail_url = reverse("medication-detail", kwargs={"pk": self.med.pk})

    def test_list_medications_valid_data(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_medication_valid(self):
        data = {"name": "Ibuprofen", "dosage_mg": 200, "prescribed_per_day": 3}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Medication.objects.count(), 2)

    def test_create_medication_invalid_dosage(self):
        data = {"name": "Invalid", "dosage_mg": 0, "prescribed_per_day": 1}
        response = self.client.post(self.list_url, data, format="json")
        self.assertFalse(response.status_code == status.HTTP_201_CREATED)
        self.assertIn("dosage_mg", response.data)

    def test_update_medication_valid(self):
        new_data = {"name": "Aspirin Max", "dosage_mg": 500, "prescribed_per_day": 1}
        response = self.client.put(self.detail_url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.med.refresh_from_db()
        self.assertEqual(self.med.name, "Aspirin Max")

    def test_delete_medication_valid(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Medication.objects.count(), 0)

    def test_delete_non_existent_medication(self):
        non_existent_url = reverse("medication-detail", kwargs={"pk": 999})
        response = self.client.delete(non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_expected_doses_valid(self):

        url = reverse("medication-expected-doses", kwargs={"pk": self.med.pk})
        response = self.client.get(f"{url}?days=10")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["medication_id"], self.med.pk)
        self.assertEqual(response.data["days"], 10)
        self.assertEqual(response.data["expected_doses"], 20)

    def test_get_expected_doses_missing_param(self):

        url = reverse("medication-expected-doses", kwargs={"pk": self.med.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_expected_doses_invalid_param(self):
        url = reverse("medication-expected-doses", kwargs={"pk": self.med.pk})
        response = self.client.get(f"{url}?days=-5")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('medtrackerapp.views.MedicationViewSet.get_object')
    @patch('medtrackerapp.models.Medication.fetch_external_info')
    def test_get_external_info_success(self, mock_fetch_info, mock_get_object):
        mock_get_object.return_value = self.med
        mock_fetch_info.return_value = {"name": "TestDrug", "manufacturer": "TestCo"}
        info_url = reverse("medication-get-external-info", kwargs={"pk": self.med.pk})
        response = self.client.get(info_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "TestDrug")
        mock_fetch_info.assert_called_once()

    @patch('medtrackerapp.views.MedicationViewSet.get_object')
    @patch('medtrackerapp.models.Medication.fetch_external_info')
    def test_get_external_info_failure(self, mock_fetch_info, mock_get_object):
        mock_get_object.return_value = self.med
        mock_fetch_info.return_value = {"error": "External API failure"}
        info_url = reverse("medication-get-external-info", kwargs={"pk": self.med.pk})
        response = self.client.get(info_url)
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn("error", response.data)


class DoseLogViewTests(APITestCase):

    def setUp(self):
        self.med = Medication.objects.create(name="PainRelief", dosage_mg=100, prescribed_per_day=2)
        self.list_url = reverse("doselog-list")

    def test_create_doselog_valid(self):
        data = {"medication": self.med.pk, "taken_at": timezone.now().isoformat(), "was_taken": True}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DoseLog.objects.count(), 1)

    def test_create_doselog_date_in_future(self):
        future_data = {"medication": self.med.pk, "taken_at": (timezone.now() + timedelta(days=1)).isoformat(),
                       "was_taken": True}
        response = self.client.post(self.list_url, future_data, format="json")
        self.assertFalse(response.status_code == status.HTTP_201_CREATED)
        self.assertIn("taken_at", response.data)

    def test_filter_doselogs_by_date_valid(self):
        DoseLog.objects.create(medication=self.med, taken_at=timezone.make_aware(timezone.datetime(2025, 11, 20, 10)))
        DoseLog.objects.create(medication=self.med, taken_at=timezone.make_aware(timezone.datetime(2025, 11, 21, 10)))
        DoseLog.objects.create(medication=self.med, taken_at=timezone.make_aware(timezone.datetime(2025, 11, 22, 10)))
        DoseLog.objects.create(medication=self.med, taken_at=timezone.make_aware(timezone.datetime(2025, 11, 23, 10)))

        start_date = date(2025, 11, 21).isoformat()
        end_date = date(2025, 11, 22).isoformat()

        filter_url = reverse("doselog-filter-by-date")
        response = self.client.get(f"{filter_url}?start={start_date}&end={end_date}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_doselogs_by_date_invalid_params(self):
        filter_url = reverse("doselog-filter-by-date")
        response = self.client.get(f"{filter_url}?start=2025-01-01")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
