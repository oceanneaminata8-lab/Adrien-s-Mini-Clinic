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

## Deploying

### Render API

1. Push this repository to GitHub.
2. In Render, create a Blueprint and select the repository. Render reads `render.yaml`.
3. Set `FRONTEND_URLS` and `FRONTEND_BASE_URL` after Vercel gives you its URL, for example:
   - `FRONTEND_URLS=https://your-clinic.vercel.app`
   - `FRONTEND_BASE_URL=https://your-clinic.vercel.app`
   - `CSRF_TRUSTED_ORIGINS=https://your-clinic.vercel.app`
4. If the generated Render service name differs from `carepoint-api`, update `ALLOWED_HOSTS` or rely on the automatically supplied Render hostname.

The API URL will resemble `https://carepoint-api.onrender.com/api`.

### Vercel Frontend

1. Import the same GitHub repository into Vercel.
2. Set the project Root Directory to `frontend`.
3. Add the environment variable:
   - `API_URL=https://your-render-service.onrender.com/api`
4. Deploy. Vercel reads `frontend/vercel.json`.

After Vercel deploys, add its final URL to the three Render frontend variables above and redeploy the Render service.

Render's filesystem is ephemeral. PostgreSQL data persists, but uploaded patient files need object storage such as S3 or Cloudinary for production use.
