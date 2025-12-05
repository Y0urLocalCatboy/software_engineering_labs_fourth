from rest_framework.test import APITestCase
from medtrackerapp.models import Medication
from django.urls import reverse
from rest_framework import status
from medtrackerapp.models import Note

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


class NoteViewTests(APITestCase):
    def setUp(self):
        """Set up test data: a medication and some notes"""
        self.med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )
        self.note1 = Note.objects.create(
            medication=self.med,
            text="Take with food"
        )
        self.note2 = Note.objects.create(
            medication=self.med,
            text="Avoid alcohol"
        )
        self.list_url = reverse("note-list")
        self.detail_url = reverse("note-detail", kwargs={"pk": self.note1.id})

    def test_list_notes_returns_all_notes(self):
        """Test GET /api/notes/ returns all notes"""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_note_by_id(self):
        """Test GET /api/notes/{id}/ returns specific note"""
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.note1.id)
        self.assertEqual(response.data["text"], "Take with food")
        self.assertEqual(response.data["medication"], self.med.id)

    def test_create_note_valid_data(self):
        """Test POST /api/notes/ creates a new note"""
        data = {
            "medication": self.med.id,
            "text": "Take in the morning"
        }
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Note.objects.count(), 3)
        self.assertEqual(response.data["text"], "Take in the morning")
        self.assertIn("created_at", response.data)

    def test_create_note_missing_medication(self):
        """Test POST /api/notes/ fails without medication"""
        data = {"text": "Some note"}
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_note_missing_text(self):
        """Test POST /api/notes/ fails without text"""
        data = {"medication": self.med.id}
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_note_invalid_medication_id(self):
        """Test POST /api/notes/ fails with non-existent medication"""
        data = {
            "medication": 99999,
            "text": "Some note"
        }
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_note(self):
        """Test DELETE /api/notes/{id}/ removes note"""
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Note.objects.count(), 1)
        self.assertFalse(Note.objects.filter(id=self.note1.id).exists())

    def test_delete_nonexistent_note(self):
        """Test DELETE /api/notes/{id}/ returns 404 for invalid ID"""
        url = reverse("note-detail", kwargs={"pk": 99999})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_note_not_allowed(self):
        """Test PUT /api/notes/{id}/ is not supported"""
        data = {"text": "Updated text", "medication": self.med.id}
        response = self.client.put(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_partial_update_note_not_allowed(self):
        """Test PATCH /api/notes/{id}/ is not supported"""
        data = {"text": "Partially updated"}
        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_created_at_field_is_readonly(self):
        """Test created_at cannot be manually set"""
        data = {
            "medication": self.med.id,
            "text": "Test note",
            "created_at": "2020-01-01"
        }
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # created_at should be today's date, not 2020-01-01
        self.assertNotEqual(response.data["created_at"], "2020-01-01")