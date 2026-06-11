from django.contrib import admin

from .models import (
    Appointment, AuditLog, AuthToken, Bill, ClinicSettings, Consultation,
    Dispensing, DoctorAvailability, InventoryItem, InvoiceItem, LabRequest,
    LabTest, Medication, Notification, Patient, PatientAttachment, Payment,
    Prescription, PrescriptionItem, Supplier, UserProfile,
)

admin.site.site_header = 'CarePoint Clinic Administration'
admin.site.site_title = 'CarePoint Admin'

for model in [
    UserProfile, AuthToken, Patient, PatientAttachment, DoctorAvailability,
    Appointment, Consultation, Medication, Prescription, PrescriptionItem,
    Bill, InvoiceItem, Payment, LabTest, LabRequest, Supplier, InventoryItem,
    Dispensing, Notification, AuditLog, ClinicSettings,
]:
    admin.site.register(model)
