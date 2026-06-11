from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from clinic.models import (
    Appointment, Bill, DoctorAvailability, InventoryItem, LabTest, Medication,
    Patient, Prescription, PrescriptionItem, Supplier, UserProfile,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample clinic records for development.'

    def handle(self, *args, **options):
        accounts = [
            ('admin@clinic.com', 'Clinic', 'Administrator', 'admin'),
            ('doctor@clinic.com', 'Sarah', 'Evans', 'doctor'),
            ('reception@clinic.com', 'Front', 'Desk', 'receptionist'),
            ('lab@clinic.com', 'Lab', 'Officer', 'lab'),
            ('pharmacy@clinic.com', 'Clinic', 'Pharmacist', 'pharmacist'),
            ('patient@clinic.com', 'Demo', 'Patient', 'patient'),
        ]
        users = {}
        for email, first_name, last_name, role in accounts:
            user, _ = User.objects.get_or_create(
                username=email,
                defaults={'email': email, 'first_name': first_name, 'last_name': last_name},
            )
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_staff = role == 'admin'
            user.is_superuser = role == 'admin'
            user.set_password('Clinic@123')
            user.save()
            UserProfile.objects.update_or_create(user=user, defaults={'role': role, 'phone': '+237 600 000 000'})
            users[role] = user

        patients = [
            ('PT-2408', 'Sarah Mitchell', 34, 'Female', 'A+', '+1 555 0192', 'Hypertension', 'Active'),
            ('PT-2407', 'James Okonkwo', 27, 'Male', 'O+', '+1 555 0284', 'Follow-up', 'Active'),
            ('PT-2406', 'Liu Wei', 22, 'Male', 'B+', '+1 555 0371', 'General Checkup', 'Active'),
            ('PT-2405', 'Maria Santos', 45, 'Female', 'AB-', '+1 555 0488', 'Diabetes', 'Active'),
            ('PT-2404', 'Ahmed Khalil', 58, 'Male', 'O-', '+1 555 0563', 'Respiratory Issue', 'Inactive'),
        ]

        patient_records = {}
        for row in patients:
            patient, _ = Patient.objects.update_or_create(
                patient_id=row[0],
                defaults={
                    'name': row[1],
                    'age': row[2],
                    'gender': row[3],
                    'blood_type': row[4],
                    'phone': row[5],
                    'condition': row[6],
                    'status': row[7],
                },
            )
            if row[0] == 'PT-2408':
                patient.address = 'Bonapriso, Douala'
                patient.emergency_contact_name = 'Michael Mitchell'
                patient.emergency_contact_phone = '+237 699 111 222'
                patient.allergies = 'Penicillin'
                patient.medical_history = 'Hypertension diagnosed in 2024.'
                patient.save()
            patient_records[row[0]] = patient

        appointments = [
            ('Sarah Mitchell', 'PT-2408', 'Dr. Sarah Evans', 'General Checkup', '2026-05-26', '09:00 AM', 'Confirmed'),
            ('James Okonkwo', 'PT-2407', 'Dr. Raj Patel', 'Follow-up', '2026-05-26', '09:45 AM', 'Confirmed'),
            ('Liu Wei', 'PT-2406', 'Dr. Sarah Evans', 'Consultation', '2026-05-26', '10:30 AM', 'Waiting'),
        ]

        for row in appointments:
            Appointment.objects.update_or_create(
                patient_name=row[0],
                time=row[5],
                defaults={
                    'patient_code': row[1],
                    'doctor': row[2],
                    'appointment_type': row[3],
                    'date': row[4],
                    'status': row[6],
                    'notes': '',
                    'doctor_user': users['doctor'],
                },
            )

        bills = [
            ('INV-0892', 'Sarah Mitchell', 185, 'Paid'),
            ('INV-0893', 'Liu Wei', 75, 'Pending'),
        ]

        for invoice_no, patient_name, amount, status in bills:
            Bill.objects.update_or_create(
                invoice_no=invoice_no,
                defaults={'patient_name': patient_name, 'amount': amount, 'status': status},
            )

        for weekday in range(5):
            DoctorAvailability.objects.update_or_create(
                doctor=users['doctor'], weekday=weekday, start_time='08:00', end_time='17:00',
                defaults={'is_active': True},
            )

        medications = [
            ('Amlodipine', 'Amlodipine', 'Tablet', '10 mg'),
            ('Paracetamol', 'Acetaminophen', 'Tablet', '500 mg'),
            ('Amoxicillin', 'Amoxicillin', 'Capsule', '500 mg'),
        ]
        supplier, _ = Supplier.objects.get_or_create(
            name='Central Medical Supplies',
            defaults={'phone': '+237 677 500 500', 'email': 'orders@cms.cm'},
        )
        medication_records = {}
        for name, generic, form, strength in medications:
            medication, _ = Medication.objects.get_or_create(
                name=name, strength=strength,
                defaults={'generic_name': generic, 'form': form},
            )
            InventoryItem.objects.update_or_create(
                medication=medication, batch_number=f'{name[:3].upper()}-2026',
                defaults={
                    'supplier': supplier, 'quantity': 30 if name != 'Amoxicillin' else 6,
                    'reorder_level': 10, 'unit_cost': 250, 'selling_price': 500,
                    'expiry_date': date.today() + timedelta(days=365),
                },
            )
            medication_records[name] = medication

        prescription_data = [
            ('PT-2408', 'Amlodipine', '10 mg', 'Once daily', '30 days', 'Take after breakfast'),
            ('PT-2407', 'Paracetamol', '500 mg', 'Twice daily', '5 days', 'Take after meals'),
            ('PT-2405', 'Amoxicillin', '500 mg', 'Three times daily', '7 days', 'Complete the full course'),
        ]
        for patient_code, medicine_name, dosage, frequency, duration, instructions in prescription_data:
            prescription, _ = Prescription.objects.get_or_create(
                patient=patient_records[patient_code],
                prescriber=users['doctor'],
                notes='Seeded prescription record',
                defaults={'status': 'Active'},
            )
            medicine = medication_records[medicine_name]
            PrescriptionItem.objects.update_or_create(
                prescription=prescription,
                medication_name=f'{medicine.name} {medicine.strength}'.strip(),
                defaults={
                    'medication': medicine,
                    'dosage': dosage,
                    'frequency': frequency,
                    'duration': duration,
                    'instructions': instructions,
                    'quantity': 1,
                },
            )

        for code, name, specimen, price in [
            ('FBC', 'Full Blood Count', 'Whole blood', 6000),
            ('GLU', 'Blood Glucose', 'Blood', 3000),
            ('MAL', 'Malaria Parasite Test', 'Blood', 2500),
        ]:
            LabTest.objects.update_or_create(
                code=code,
                defaults={'name': name, 'specimen': specimen, 'price': price, 'active': True},
            )

        self.stdout.write(self.style.SUCCESS(
            'Sample clinic data is ready. Login with admin@clinic.com / Clinic@123.'
        ))
