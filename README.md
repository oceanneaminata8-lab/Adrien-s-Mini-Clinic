# CarePoint Mini Clinic

Angular and Django REST clinic management system with expiring bearer sessions and role-based access.

## Modules

- Secure registration, login, logout, password reset, and eight-hour sessions
- Patient demographics, emergency contacts, allergies, history, attachments, and visits
- Doctor availability, appointment rescheduling, reminders, and booking conflict prevention
- Consultations and structured prescriptions
- Invoices, services, discounts, partial payments, receipts, and balances
- Laboratory test catalogue, sample tracking, results, and doctor review
- Pharmacy catalogue, suppliers, batches, expiry dates, dispensing, and low-stock alerts
- Revenue, diagnosis, patient, and doctor-workload reports with CSV export
- In-app/email/SMS/WhatsApp notification queue
- Role permissions, security headers, audit logs, and SQLite backup command

External SMS and WhatsApp delivery requires connecting a provider. The system securely queues those messages and tracks their status. Production deployments should use HTTPS, a strong `DJANGO_SECRET_KEY`, and encrypted database/disk storage.

## Backend

```cmd
cd backend
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py seed_clinic
.venv\Scripts\python.exe manage.py runserver
```

API: `http://127.0.0.1:8000/api/`

## Frontend

```cmd
cd frontend
npm install
npm start
```

Application: `http://localhost:4200`

## Demo Accounts

All seeded accounts use password `Clinic@123`.

| Role | Email |
| --- | --- |
| Administrator | `admin@clinic.com` |
| Doctor | `doctor@clinic.com` |
| Receptionist | `reception@clinic.com` |
| Laboratory | `lab@clinic.com` |
| Pharmacist | `pharmacy@clinic.com` |
| Patient | `patient@clinic.com` |

Public registration always creates a patient account. Staff roles must be assigned by an administrator.

## Backup

Create a consistent database backup:

```cmd
cd backend
.venv\Scripts\python.exe manage.py backup_clinic
```

Backups are written to `backend/backups/`.

## Production Security

Set environment variables before deployment:

```cmd
set DJANGO_SECRET_KEY=replace-with-a-long-random-secret
set DJANGO_DEBUG=false
```

Use HTTPS and encrypted disk/database storage in production. Django passwords are hashed; raw passwords are never stored.
