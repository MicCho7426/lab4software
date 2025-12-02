from django.test import TestCase
from medtrackerapp.services import DrugInfoService
from medtrackerapp.models import Medication
from rest_framework import status
import requests_mock


MOCK_SUCCESS_DATA = {
    "results": [{
        "drug_brand_name": ["Test Brand"],
        "manufacturer_name": ["Test Mfgr"],
        "substance_name": ["Test Substance"]
    }]
}


class DrugInfoServiceTests(TestCase):

    def setUp(self):
        self.service = DrugInfoService()
        self.medication = Medication(name="TestDrug", dosage_mg=100, prescribed_per_day=1)

    def test_fetch_external_info_success(self):
        with requests_mock.Mocker() as m:
            m.get(DrugInfoService.BASE_URL, status_code=status.HTTP_200_OK, json=MOCK_SUCCESS_DATA)
            result = self.service.fetch_external_info(self.medication.name)
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("brand_name"), "Test Brand")
            self.assertEqual(m.call_count, 1)

    def test_fetch_external_info_http_error(self):
        with requests_mock.Mocker() as m:
            m.get(DrugInfoService.BASE_URL, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            result = self.service.fetch_external_info(self.medication.name)
            self.assertIn('error', result)
            self.assertIn('HTTP Error', result['error'])
            self.assertEqual(m.call_count, 1)

    def test_fetch_external_info_connection_error(self):
        with requests_mock.Mocker() as m:
            m.get(DrugInfoService.BASE_URL, exc=requests_mock.exceptions.NoMockAddress)
            result = self.service.fetch_external_info(self.medication.name)
            self.assertIn('error', result)
            self.assertIn('Connection Error', result['error'])
            self.assertEqual(m.call_count, 1)
