from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from medtrackerapp.models import Medication, DoctorNote
from django.utils import timezone


class DoctorNoteTests(APITestCase):

    def setUp(self):

        self.med = Medication.objects.create(name="TestMed", dosage_mg=100, prescribed_per_day=1)

        self.list_url = reverse("doctornote-list")

    def test_create_note_valid(self):
        """test of creating a note"""
        data = {
            "medication": self.med.id,
            "note": "Take with food",
            "created_at": timezone.now().date()
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DoctorNote.objects.count(), 1)
        self.assertEqual(DoctorNote.objects.get().note, "Take with food")

    def test_list_notes(self):
        """test of notes"""
        DoctorNote.objects.create(medication=self.med, note="Note 1", created_at=timezone.now().date())
        DoctorNote.objects.create(medication=self.med, note="Note 2", created_at=timezone.now().date())

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_delete_note(self):
        """test deleting note"""
        note = DoctorNote.objects.create(medication=self.med, note="To delete", created_at=timezone.now().date())
        detail_url = reverse("doctornote-detail", kwargs={"pk": note.pk})

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(DoctorNote.objects.count(), 0)

    def test_update_note_not_allowed(self):
        """test which checks if the edition is possible."""
        note = DoctorNote.objects.create(medication=self.med, note="Original", created_at=timezone.now().date())
        detail_url = reverse("doctornote-detail", kwargs={"pk": note.pk})

        data = {"note": "Updated"}
        response = self.client.put(detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)