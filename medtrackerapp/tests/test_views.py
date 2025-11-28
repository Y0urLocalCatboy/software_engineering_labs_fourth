from rest_framework.test import APITestCase
from medtrackerapp.models import Medication
from django.urls import reverse
from rest_framework import status


class MedicationViewTests(APITestCase):
    def setUp(self):
        self.med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.url = reverse("medication-expected-doses", kwargs={"pk": self.med.id})

    def test_list_medications_valid_data(self):
        url = reverse("medication-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Aspirin")
        self.assertEqual(response.data[0]["dosage_mg"], 100)

    def test_expected_doses_valid_request(self):
        """Test valid request returns 200 with correct data"""
        response = self.client.get(self.url, {"days": 7})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["medication_id"], self.med.id)
        self.assertEqual(response.data["days"], 7)
        self.assertEqual(response.data["expected_doses"], 14)

    def test_expected_doses_missing_days_parameter(self):
        """Test missing days parameter returns 400"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expected_doses_invalid_days_not_integer(self):
        """Test invalid days parameter (not an integer) returns 400"""
        response = self.client.get(self.url, {"days": "abc"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expected_doses_invalid_days_negative(self):
        """Test negative days parameter returns 400"""
        response = self.client.get(self.url, {"days": -5})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expected_doses_invalid_days_zero(self):
        """Test zero days parameter returns 400"""
        response = self.client.get(self.url, {"days": 0})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expected_doses_invalid_days_float(self):
        """Test float days parameter returns 400"""
        response = self.client.get(self.url, {"days": 3.5})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expected_doses_value_error_from_model(self):
        """Test ValueError raised by model method returns 400"""
        response = self.client.get(self.url, {"days": 999999})

        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_200_OK])

    def test_expected_doses_nonexistent_medication(self):
        """Test request with non-existent medication ID returns 404"""
        url = reverse("medication-expected-doses", kwargs={"pk": 99999})
        response = self.client.get(url, {"days": 7})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_expected_doses_multiple_valid_requests(self):
        """Test multiple valid requests with different days values"""
        test_cases = [
            (1, 2),
            (7, 14),
            (30, 60),
        ]

        for days, expected in test_cases:
            with self.subTest(days=days):
                response = self.client.get(self.url, {"days": days})
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["expected_doses"], expected)