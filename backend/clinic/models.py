import hashlib
import secrets
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('doctor', 'Doctor'),
        ('receptionist', 'Receptionist'),
        ('patient', 'Patient'),
        ('lab', 'Laboratory'),
        ('pharmacist', 'Pharmacist'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clinic_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    phone = models.CharField(max_length=30, blank=True)
    must_change_password = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.role})'


class AuthToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clinic_tokens')
    key_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def issue(cls, user, lifetime_hours=8):
        raw_key = secrets.token_urlsafe(40)
        cls.objects.create(
            user=user,
            key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
            expires_at=timezone.now() + timedelta(hours=lifetime_hours),
        )
        return raw_key

    @classmethod
    def digest(cls, raw_key):
        return hashlib.sha256(raw_key.encode()).hexdigest()


class Patient(models.Model):
    patient_id = models.CharField(max_length=20, unique=True, blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='patient_record'
    )
    name = models.CharField(max_length=120)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(default=0)
    gender = models.CharField(max_length=20)
    blood_type = models.CharField(max_length=5, blank=True)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=120, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    allergies = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    condition = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.date_of_birth:
            today = timezone.localdate()
            self.age = today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        if not self.patient_id:
            last_patient = Patient.objects.order_by('-id').first()
            try:
                new_num = int(last_patient.patient_id.split('-')[1]) + 1 if last_patient else 2401
            except (IndexError, ValueError):
                new_num = Patient.objects.count() + 2401
            self.patient_id = f'PT-{new_num}'
            while Patient.objects.filter(patient_id=self.patient_id).exists():
                new_num += 1
                self.patient_id = f'PT-{new_num}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PatientAttachment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='attachments')
    title = models.CharField(max_length=120)
    file = models.FileField(upload_to='patient_attachments/%Y/%m/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class DoctorAvailability(models.Model):
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='availability_slots'
    )
    weekday = models.PositiveSmallIntegerField(choices=[(i, day) for i, day in enumerate(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    )])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'weekday', 'start_time', 'end_time')


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, null=True, blank=True, on_delete=models.SET_NULL, related_name='appointments')
    doctor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='doctor_appointments'
    )
    patient_name = models.CharField(max_length=120)
    patient_code = models.CharField(max_length=20, blank=True)
    doctor = models.CharField(max_length=120)
    appointment_type = models.CharField(max_length=80)
    date = models.DateField()
    time = models.CharField(max_length=20)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Pending')
    notes = models.TextField(blank=True)
    reminder_sent = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_appointments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time', 'time']

    def __str__(self):
        return f'{self.patient_name} with {self.doctor}'


class Consultation(models.Model):
    patient = models.ForeignKey(Patient, null=True, blank=True, on_delete=models.SET_NULL, related_name='visits')
    appointment = models.OneToOneField(
        Appointment, null=True, blank=True, on_delete=models.SET_NULL, related_name='consultation'
    )
    clinician = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='consultations'
    )
    patient_name = models.CharField(max_length=120)
    doctor = models.CharField(max_length=120)
    symptoms = models.TextField(blank=True)
    diagnosis = models.TextField()
    treatment_notes = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    blood_pressure = models.CharField(max_length=20, blank=True)
    heart_rate = models.PositiveSmallIntegerField(null=True, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    oxygen_saturation = models.PositiveSmallIntegerField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Consultation for {self.patient_name}'


class Medication(models.Model):
    name = models.CharField(max_length=120)
    generic_name = models.CharField(max_length=120, blank=True)
    form = models.CharField(max_length=50, blank=True)
    strength = models.CharField(max_length=50, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return ' '.join(filter(None, [self.name, self.strength]))


class Prescription(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    consultation = models.ForeignKey(
        Consultation, null=True, blank=True, on_delete=models.SET_NULL, related_name='prescriptions'
    )
    prescriber = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medication = models.ForeignKey(Medication, null=True, blank=True, on_delete=models.SET_NULL)
    medication_name = models.CharField(max_length=150)
    dosage = models.CharField(max_length=120)
    frequency = models.CharField(max_length=120)
    duration = models.CharField(max_length=120)
    instructions = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)


class Bill(models.Model):
    patient = models.ForeignKey(Patient, null=True, blank=True, on_delete=models.SET_NULL, related_name='invoices')
    patient_name = models.CharField(max_length=120)
    invoice_no = models.CharField(max_length=30, unique=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default='Pending')
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.invoice_no


class InvoiceItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    service = models.CharField(max_length=150)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    @property
    def total(self):
        return self.quantity * self.unit_price


class Payment(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    method = models.CharField(max_length=30, choices=[
        ('cash', 'Cash'), ('card', 'Card'), ('mobile_money', 'Mobile Money'), ('bank', 'Bank Transfer')
    ])
    reference = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    paid_at = models.DateTimeField(default=timezone.now)


class LabTest(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=30, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    specimen = models.CharField(max_length=80, blank=True)
    reference_range = models.CharField(max_length=120, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class LabRequest(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_requests')
    test = models.ForeignKey(LabTest, on_delete=models.PROTECT)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='requested_lab_tests'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_lab_tests'
    )
    sample_id = models.CharField(max_length=40, unique=True, blank=True)
    status = models.CharField(max_length=30, default='Requested')
    result = models.TextField(blank=True)
    result_value = models.CharField(max_length=120, blank=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.sample_id:
            self.sample_id = f'LAB-{timezone.now():%y%m%d}-{secrets.token_hex(3).upper()}'
        super().save(*args, **kwargs)


class Supplier(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT, related_name='stock_batches')
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL)
    batch_number = models.CharField(max_length=80)
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('medication', 'batch_number')

    @property
    def low_stock(self):
        return self.quantity <= self.reorder_level


class Dispensing(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='dispensings')
    prescription_item = models.ForeignKey(
        PrescriptionItem, null=True, blank=True, on_delete=models.SET_NULL, related_name='dispensings'
    )
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name='dispensings')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    dispensed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    dispensed_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    CHANNELS = [('in_app', 'In app'), ('email', 'Email'), ('sms', 'SMS'), ('whatsapp', 'WhatsApp')]
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name='notifications'
    )
    patient = models.ForeignKey(Patient, null=True, blank=True, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, null=True, blank=True, on_delete=models.CASCADE)
    channel = models.CharField(max_length=20, choices=CHANNELS, default='in_app')
    destination = models.CharField(max_length=150, blank=True)
    subject = models.CharField(max_length=150, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, default='Queued')
    scheduled_for = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=50)
    entity_type = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80, blank=True)
    summary = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class ClinicSettings(models.Model):
    clinic_name = models.CharField(max_length=120, default='Mini Clinic')
    address = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    logo_url = models.TextField(blank=True)

    def __str__(self):
        return self.clinic_name
