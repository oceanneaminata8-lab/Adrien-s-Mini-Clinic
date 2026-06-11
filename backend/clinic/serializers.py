from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import (
    Appointment, AuditLog, Bill, ClinicSettings, Consultation, Dispensing,
    DoctorAvailability, InventoryItem, InvoiceItem, LabRequest, LabTest,
    Medication, Notification, Patient, PatientAttachment, Payment,
    Prescription, PrescriptionItem, Supplier, UserProfile,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone']

    def get_role(self, obj):
        if obj.is_superuser:
            return 'admin'
        return getattr(getattr(obj, 'clinic_profile', None), 'role', 'patient')

    def get_phone(self, obj):
        return getattr(getattr(obj, 'clinic_profile', None), 'phone', '')


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30)
    password = serializers.CharField(min_length=8, write_only=True)
    role = serializers.HiddenField(default='patient')

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        names = validated_data['full_name'].strip().split(maxsplit=1)
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=names[0],
            last_name=names[1] if len(names) > 1 else '',
        )
        UserProfile.objects.create(user=user, role='patient', phone=validated_data['phone'])
        Patient.objects.create(
            user=user, name=validated_data['full_name'], email=validated_data['email'],
            phone=validated_data['phone'], gender='Not specified',
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['email'].lower(), password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        attrs['user'] = user
        return attrs


class PatientAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientAttachment
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'uploaded_at']


class PatientSerializer(serializers.ModelSerializer):
    attachments = PatientAttachmentSerializer(many=True, read_only=True)
    visits_count = serializers.IntegerField(source='visits.count', read_only=True)

    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ['patient_id', 'created_at', 'updated_at']


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)

    class Meta:
        model = DoctorAvailability
        fields = '__all__'


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        doctor = attrs.get('doctor_user') or getattr(self.instance, 'doctor_user', None)
        date = attrs.get('date') or getattr(self.instance, 'date', None)
        start = attrs.get('start_time') or getattr(self.instance, 'start_time', None)
        end = attrs.get('end_time') or getattr(self.instance, 'end_time', None)
        if start and end and start >= end:
            raise serializers.ValidationError({'end_time': 'End time must be after start time.'})
        if doctor and date and start and end:
            clashes = Appointment.objects.filter(
                doctor_user=doctor, date=date,
                status__in=['Pending', 'Confirmed', 'Waiting'],
                start_time__lt=end, end_time__gt=start,
            )
            if self.instance:
                clashes = clashes.exclude(pk=self.instance.pk)
            if clashes.exists():
                raise serializers.ValidationError('This doctor already has an appointment in that time range.')
        return attrs


class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = '__all__'
        read_only_fields = ['clinician', 'created_at', 'updated_at']


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'


class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = '__all__'
        read_only_fields = ['prescription']


class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True)
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    prescriber_name = serializers.CharField(source='prescriber.get_full_name', read_only=True)

    class Meta:
        model = Prescription
        fields = '__all__'
        read_only_fields = ['prescriber', 'created_at']

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop('items', [])
        prescription = Prescription.objects.create(**validated_data)
        for item in items:
            PrescriptionItem.objects.create(prescription=prescription, **item)
        return prescription


class InvoiceItemSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceItem
        fields = '__all__'
        read_only_fields = ['bill']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['received_by', 'paid_at']


class BillSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, required=False)
    payments = PaymentSerializer(many=True, read_only=True)
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']
        extra_kwargs = {'amount': {'required': False}}

    def get_balance(self, obj):
        paid = sum(payment.amount for payment in obj.payments.all())
        return max(obj.amount - paid, 0)

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop('items', [])
        validated_data.setdefault('amount', 0)
        bill = Bill.objects.create(**validated_data)
        if items:
            subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
            for item in items:
                InvoiceItem.objects.create(bill=bill, **item)
            bill.subtotal = subtotal
            bill.amount = max(subtotal - bill.discount, 0)
            bill.save(update_fields=['subtotal', 'amount'])
        return bill


class LabTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTest
        fields = '__all__'


class LabRequestSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    test_name = serializers.CharField(source='test.name', read_only=True)

    class Meta:
        model = LabRequest
        fields = '__all__'
        read_only_fields = ['requested_by', 'reviewed_by', 'sample_id', 'created_at']


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class InventoryItemSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='medication.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = '__all__'


class DispensingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispensing
        fields = '__all__'
        read_only_fields = ['dispensed_by', 'dispensed_at']

    def validate(self, attrs):
        if attrs['inventory_item'].quantity < attrs['quantity']:
            raise serializers.ValidationError('Insufficient stock for this dispensing.')
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        item = InventoryItem.objects.select_for_update().get(pk=validated_data['inventory_item'].pk)
        if item.quantity < validated_data['quantity']:
            raise serializers.ValidationError('Insufficient stock for this dispensing.')
        item.quantity -= validated_data['quantity']
        item.save(update_fields=['quantity'])
        validated_data['inventory_item'] = item
        return Dispensing.objects.create(**validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['sent_at', 'created_at']


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.get_full_name', read_only=True)

    class Meta:
        model = AuditLog
        fields = '__all__'


class ClinicSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicSettings
        fields = '__all__'
