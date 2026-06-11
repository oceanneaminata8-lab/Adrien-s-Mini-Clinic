from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import (
    Appointment, AuthToken, Bill, InventoryItem, Medication, Patient,
    UserProfile,
)

User = get_user_model()


class ClinicApiTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin@test.com', email='admin@test.com', password='StrongPass123'
        )
        UserProfile.objects.create(user=self.admin, role='admin')
        self.doctor = User.objects.create_user(
            username='doctor@test.com', email='doctor@test.com', password='StrongPass123',
            first_name='Test', last_name='Doctor',
        )
        UserProfile.objects.create(user=self.doctor, role='doctor')
        self.patient_user = User.objects.create_user(
            username='patient@test.com', email='patient@test.com', password='StrongPass123'
        )
        UserProfile.objects.create(user=self.patient_user, role='patient')
        self.patient = Patient.objects.create(
            user=self.patient_user, name='Test Patient', gender='Female', phone='600000000'
        )
        self.client = APIClient()

    def login(self, email='admin@test.com', password='StrongPass123'):
        response = self.client.post('/api/auth/login/', {'email': email, 'password': password}, format='json')
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['token']}")
        return response

    def test_login_issues_expiring_token_and_logout_revokes_it(self):
        response = self.login()
        self.assertEqual(response.data['user']['role'], 'admin')
        self.assertEqual(AuthToken.objects.count(), 1)
        logout = self.client.post('/api/auth/logout/')
        self.assertEqual(logout.status_code, 204)
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_patient_cannot_read_another_patient_record(self):
        Patient.objects.create(name='Other Patient', gender='Male', phone='611111111')
        self.login('patient@test.com')
        response = self.client.get('/api/patients/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Patient')

    def test_double_booking_is_rejected(self):
        self.login()
        Appointment.objects.create(
            patient=self.patient, doctor_user=self.doctor, patient_name=self.patient.name,
            patient_code=self.patient.patient_id, doctor='Test Doctor',
            appointment_type='Consultation', date=date.today(), time='09:00 AM',
            start_time=time(9, 0), end_time=time(10, 0), status='Confirmed',
        )
        response = self.client.post('/api/appointments/', {
            'patient': self.patient.pk,
            'doctor_user': self.doctor.pk,
            'patient_name': self.patient.name,
            'patient_code': self.patient.patient_id,
            'doctor': 'Test Doctor',
            'appointment_type': 'Follow-up',
            'date': str(date.today()),
            'time': '09:30 AM',
            'start_time': '09:30:00',
            'end_time': '10:30:00',
            'status': 'Confirmed',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_payment_updates_invoice_status(self):
        self.login()
        bill = Bill.objects.create(
            patient=self.patient, patient_name=self.patient.name,
            invoice_no='INV-TEST', amount=10000, subtotal=10000, status='Pending',
        )
        partial = self.client.post(f'/api/bills/{bill.pk}/pay/', {
            'amount': 4000, 'method': 'cash',
        }, format='json')
        self.assertEqual(partial.status_code, 201)
        bill.refresh_from_db()
        self.assertEqual(bill.status, 'Partially Paid')
        paid = self.client.post(f'/api/bills/{bill.pk}/pay/', {
            'amount': 6000, 'method': 'mobile_money',
        }, format='json')
        self.assertEqual(paid.status_code, 201)
        bill.refresh_from_db()
        self.assertEqual(bill.status, 'Paid')

    def test_dispensing_cannot_exceed_stock(self):
        self.login()
        medicine = Medication.objects.create(name='Test Medicine')
        stock = InventoryItem.objects.create(
            medication=medicine, batch_number='B-1', quantity=2,
            expiry_date=timezone.localdate() + timedelta(days=30),
        )
        response = self.client.post('/api/dispensing/', {
            'patient': self.patient.pk,
            'inventory_item': stock.pk,
            'quantity': 3,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        stock.refresh_from_db()
        self.assertEqual(stock.quantity, 2)

    def test_patient_role_cannot_access_billing(self):
        self.login('patient@test.com')
        response = self.client.get('/api/bills/')
        self.assertEqual(response.status_code, 403)

    def test_doctor_cannot_access_billing_or_inventory(self):
        self.login('doctor@test.com')
        self.assertEqual(self.client.get('/api/bills/').status_code, 403)
        self.assertEqual(self.client.get('/api/inventory/').status_code, 403)

    def test_admin_can_create_medicine_inventory_and_invoice(self):
        self.login()
        medicine = self.client.post('/api/medications/', {
            'name': 'Metformin', 'generic_name': 'Metformin',
            'form': 'Tablet', 'strength': '500 mg', 'active': True,
        }, format='json')
        self.assertEqual(medicine.status_code, 201)
        stock = self.client.post('/api/inventory/', {
            'medication': medicine.data['id'], 'batch_number': 'MET-001',
            'quantity': 50, 'reorder_level': 10, 'unit_cost': 100,
            'selling_price': 200, 'expiry_date': str(timezone.localdate() + timedelta(days=365)),
        }, format='json')
        self.assertEqual(stock.status_code, 201)
        invoice = self.client.post('/api/bills/', {
            'patient': self.patient.pk, 'patient_name': self.patient.name,
            'invoice_no': 'INV-CREATE', 'discount': 500, 'status': 'Pending',
            'items': [{'service': 'Consultation', 'quantity': 1, 'unit_price': 5000}],
        }, format='json')
        self.assertEqual(invoice.status_code, 201)
        self.assertEqual(float(invoice.data['amount']), 4500)
