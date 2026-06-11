import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';

type Role = 'admin' | 'doctor' | 'patient';
type Page = 'dashboard' | 'patients' | 'appointments' | 'consultation' | 'prescriptions' | 'billing' |
  'pharmacy' | 'patient-booking' | 'settings';
type NoticeType = 'success' | 'error' | 'info';
type AuthView = 'landing' | 'login' | 'register' | 'forgot' | 'reset';

interface AuthUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
}

interface AuthResponse {
  token: string;
  expires_in: number;
  user: AuthUser;
}

interface Patient {
  id: number;
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  blood_type: string;
  phone: string;
  email?: string;
  date_of_birth?: string;
  address?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  allergies?: string;
  medical_history?: string;
  condition: string;
  status: string;
}

interface Appointment {
  id: number;
  patient_name: string;
  patient_code: string;
  doctor: string;
  appointment_type: string;
  date: string;
  time: string;
  status: string;
  notes: string;
}

interface Bill {
  id: number;
  patient_name: string;
  invoice_no: string;
  amount: number;
  status: string;
}

interface ClinicSettings {
  id?: number;
  clinic_name: string;
  address: string;
  contact_email: string;
  logo_url: string;
}

interface Notice {
  message: string;
  type: NoticeType;
}

@Component({
  selector: 'app-root',
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  private apiUrl = (
    (globalThis as typeof globalThis & {
      __CAREPOINT_CONFIG__?: { apiUrl?: string };
    }).__CAREPOINT_CONFIG__?.apiUrl || 'http://127.0.0.1:8000/api'
  ).replace(/\/+$/, '');
  private noticeTimer?: ReturnType<typeof setTimeout>;
  currentUser: AuthUser | null = null;

  loggedIn = false;
  authView: AuthView = 'landing';
  role: Role = 'admin';
  activePage: Page = 'dashboard';
  searchText = '';
  notice: Notice | null = null;
  selectedPatientId = 1;
  navOpen = false;

  readonly today = new Date();
  readonly todayIso = this.today.toISOString().slice(0, 10);
  readonly pageLabels: Record<Page, string> = {
    dashboard: 'Clinic overview',
    patients: 'Patient records',
    appointments: 'Appointments',
    consultation: 'Consultation room',
    prescriptions: 'Prescriptions',
    billing: 'Billing and payments',
    pharmacy: 'Pharmacy and inventory',
    'patient-booking': 'Book an appointment',
    settings: 'Clinic settings'
  };

  login = {
    email: 'admin@clinic.com',
    password: 'Clinic@123',
    role: 'admin' as Role
  };

  resetEmail = '';
  resetCredentials = { uid: '', token: '', password: '', confirmPassword: '' };

  registration = {
    fullName: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    role: 'patient' as Role
  };

  newPatient = {
    name: '',
    age: 0,
    gender: 'Female',
    blood_type: 'A+',
    phone: '',
    condition: '',
    email: '',
    date_of_birth: '',
    address: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    allergies: '',
    medical_history: '',
    status: 'Active'
  };

  booking = this.emptyBooking();

  consultation = {
    symptoms: 'Headache, fatigue and occasional dizziness.',
    diagnosis: 'Essential hypertension with elevated blood pressure.',
    treatment_notes: 'Review medication adherence. Follow up in two weeks.',
    prescription: 'Amlodipine 10 mg, once daily for 30 days.'
  };

  clinicSettings: ClinicSettings = {
    clinic_name: 'CarePoint Mini Clinic',
    address: '12 Health Avenue, Douala',
    contact_email: 'hello@carepoint.cm',
    logo_url: ''
  };

  patients: Patient[] = [
    { id: 1, patient_id: 'PT-2408', name: 'Sarah Mitchell', age: 34, gender: 'Female', blood_type: 'A+', phone: '+237 6 75 01 92 44', condition: 'Hypertension', status: 'Active' },
    { id: 2, patient_id: 'PT-2407', name: 'James Okonkwo', age: 27, gender: 'Male', blood_type: 'O+', phone: '+237 6 98 20 84 10', condition: 'Follow-up', status: 'Active' },
    { id: 3, patient_id: 'PT-2406', name: 'Liu Wei', age: 22, gender: 'Male', blood_type: 'B+', phone: '+237 6 70 33 71 02', condition: 'General checkup', status: 'Active' },
    { id: 4, patient_id: 'PT-2405', name: 'Maria Santos', age: 45, gender: 'Female', blood_type: 'AB-', phone: '+237 6 55 04 88 33', condition: 'Diabetes', status: 'Active' },
    { id: 5, patient_id: 'PT-2404', name: 'Ahmed Khalil', age: 58, gender: 'Male', blood_type: 'O-', phone: '+237 6 90 05 63 21', condition: 'Respiratory issue', status: 'Inactive' }
  ];

  appointments: Appointment[] = [
    { id: 1, patient_name: 'Sarah Mitchell', patient_code: 'PT-2408', doctor: 'Dr. Sarah Evans', appointment_type: 'General checkup', date: this.todayIso, time: '09:00 AM', status: 'Completed', notes: '' },
    { id: 2, patient_name: 'James Okonkwo', patient_code: 'PT-2407', doctor: 'Dr. Raj Patel', appointment_type: 'Follow-up', date: this.todayIso, time: '09:45 AM', status: 'Confirmed', notes: '' },
    { id: 3, patient_name: 'Liu Wei', patient_code: 'PT-2406', doctor: 'Dr. Sarah Evans', appointment_type: 'Consultation', date: this.todayIso, time: '10:30 AM', status: 'Waiting', notes: '' },
    { id: 4, patient_name: 'Maria Santos', patient_code: 'PT-2405', doctor: 'Dr. Angela Kim', appointment_type: 'Diabetes review', date: this.todayIso, time: '11:15 AM', status: 'Confirmed', notes: '' }
  ];

  bills: Bill[] = [
    { id: 1, patient_name: 'Sarah Mitchell', invoice_no: 'INV-0892', amount: 18500, status: 'Paid' },
    { id: 2, patient_name: 'Liu Wei', invoice_no: 'INV-0893', amount: 7500, status: 'Pending' },
    { id: 3, patient_name: 'Maria Santos', invoice_no: 'INV-0894', amount: 12000, status: 'Paid' }
  ];
  medications: any[] = [];
  prescriptions: any[] = [];
  inventory: any[] = [];
  selectedPrescriptionPatientId = 0;
  showMedicineForm = false;
  showInvoiceForm = false;

  newMedicine = {
    name: '', generic_name: '', form: 'Tablet', strength: '',
    batch_number: '', quantity: 0, reorder_level: 10,
    unit_cost: 0, selling_price: 0, expiry_date: ''
  };

  newInvoice = {
    patient: 0,
    discount: 0,
    due_date: this.todayIso,
    notes: '',
    items: [{ service: 'Consultation', quantity: 1, unit_price: 0 }]
  };

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    const query = new URLSearchParams(window.location.search);
    const resetUid = query.get('reset_uid');
    const resetToken = query.get('reset_token');
    if (resetUid && resetToken) {
      this.resetCredentials.uid = resetUid;
      this.resetCredentials.token = resetToken;
      this.authView = 'reset';
      return;
    }
    if (localStorage.getItem('clinic_token')) {
      this.http.get<AuthUser>(`${this.apiUrl}/auth/me/`).subscribe({
        next: user => this.finishSignIn(user),
        error: () => this.clearSession()
      });
    }
  }

  signIn(): void {
    if (!this.login.email || !this.login.password) {
      this.showNotice('Enter your email and password to continue.', 'error');
      return;
    }

    this.http.post<AuthResponse>(`${this.apiUrl}/auth/login/`, {
      email: this.login.email,
      password: this.login.password
    }).subscribe({
      next: response => {
        localStorage.setItem('clinic_token', response.token);
        localStorage.setItem('clinic_token_expires', String(Date.now() + response.expires_in * 1000));
        this.finishSignIn(response.user);
        this.showNotice(`Welcome to the ${response.user.role} workspace.`, 'success');
      },
      error: error => this.showNotice(
        error.error?.non_field_errors?.[0] || error.error?.detail || 'Invalid email or password.',
        'error'
      )
    });
  }

  private finishSignIn(user: AuthUser): void {
    this.currentUser = user;
    this.role = user.role;
    this.login.role = user.role;
    this.loggedIn = true;
    this.activePage = this.role === 'patient' ? 'patient-booking' : 'dashboard';
    this.loadData();
  }

  showAuth(view: AuthView): void {
    this.authView = view;
    this.notice = null;
  }

  register(): void {
    const form = this.registration;
    if (!form.fullName.trim() || !form.email.trim() || !form.phone.trim() || !form.password) {
      this.showNotice('Complete all required registration fields.', 'error');
      return;
    }
    if (form.password.length < 6) {
      this.showNotice('Use at least 6 characters for your password.', 'error');
      return;
    }
    if (form.password !== form.confirmPassword) {
      this.showNotice('The passwords do not match.', 'error');
      return;
    }

    this.http.post<AuthUser>(`${this.apiUrl}/auth/register/`, {
      full_name: form.fullName,
      email: form.email,
      phone: form.phone,
      password: form.password
    }).subscribe({
      next: () => {
        this.login.email = form.email;
        this.login.password = form.password;
        this.login.role = 'patient';
        this.authView = 'login';
        this.registration = {
          fullName: '', email: '', phone: '', password: '',
          confirmPassword: '', role: 'patient'
        };
        this.showNotice('Account created. Sign in to continue.', 'success');
      },
      error: error => this.showNotice(
        error.error?.email?.[0] || error.error?.password?.[0] || 'Registration failed.',
        'error'
      )
    });
  }

  logout(): void {
    this.http.post(`${this.apiUrl}/auth/logout/`, {}).subscribe({
      next: () => this.clearSession(),
      error: () => this.clearSession()
    });
  }

  requestPasswordReset(): void {
    if (!this.resetEmail.trim()) {
      this.showNotice('Enter the email address for your account.', 'error');
      return;
    }
    this.http.post<{ detail: string }>(`${this.apiUrl}/auth/password-reset/`, {
      email: this.resetEmail
    }).subscribe({
      next: response => this.showNotice(response.detail, 'success'),
      error: () => this.showNotice('Unable to request a password reset.', 'error')
    });
  }

  confirmPasswordReset(): void {
    const form = this.resetCredentials;
    if (form.password.length < 8 || form.password !== form.confirmPassword) {
      this.showNotice('Use matching passwords with at least 8 characters.', 'error');
      return;
    }
    this.http.post<{ detail: string }>(`${this.apiUrl}/auth/password-reset-confirm/`, {
      uid: form.uid, token: form.token, password: form.password
    }).subscribe({
      next: response => {
        window.history.replaceState({}, '', window.location.pathname);
        this.authView = 'login';
        this.showNotice(response.detail, 'success');
      },
      error: error => this.showNotice(error.error?.detail || 'The reset link is invalid or expired.', 'error')
    });
  }

  private clearSession(): void {
    localStorage.removeItem('clinic_token');
    localStorage.removeItem('clinic_token_expires');
    this.currentUser = null;
    this.loggedIn = false;
    this.authView = 'landing';
    this.searchText = '';
    this.navOpen = false;
  }

  go(page: Page): void {
    if (!this.allowedPages.includes(page)) {
      this.showNotice('Your account does not have access to that page.', 'error');
      return;
    }
    this.activePage = page;
    this.searchText = '';
    this.navOpen = false;
  }

  toggleNav(): void {
    this.navOpen = !this.navOpen;
  }

  closeNav(): void {
    this.navOpen = false;
  }

  loadData(): void {
    if (['admin', 'doctor', 'patient'].includes(this.role)) {
      this.http.get<Patient[]>(`${this.apiUrl}/patients/`).subscribe({
        next: data => this.patients = data,
        error: () => {}
      });
    }
    this.http.get<Appointment[]>(`${this.apiUrl}/appointments/`).subscribe({
      next: data => this.appointments = data,
      error: () => {}
    });
    if (this.role === 'admin') {
      this.http.get<Bill[]>(`${this.apiUrl}/bills/`).subscribe({ next: data => this.bills = data, error: () => {} });
      this.http.get<ClinicSettings>(`${this.apiUrl}/settings/`).subscribe({
        next: data => this.clinicSettings = data, error: () => {}
      });
    }
    if (['admin', 'doctor'].includes(this.role)) {
      this.http.get<any[]>(`${this.apiUrl}/medications/`).subscribe({ next: data => this.medications = data, error: () => {} });
      this.http.get<any[]>(`${this.apiUrl}/prescriptions/`).subscribe({ next: data => this.prescriptions = data, error: () => {} });
    }
    if (this.role === 'admin') {
      this.http.get<any[]>(`${this.apiUrl}/inventory/`).subscribe({ next: data => this.inventory = data, error: () => {} });
    }
  }

  get allowedPages(): Page[] {
    if (this.role === 'patient') return ['patient-booking'];
    if (this.role === 'doctor') {
      return ['dashboard', 'patients', 'appointments', 'consultation', 'prescriptions', 'patient-booking'];
    }
    if (this.role === 'admin') {
      return ['dashboard', 'patients', 'appointments', 'consultation', 'prescriptions', 'billing', 'pharmacy', 'patient-booking', 'settings'];
    }
    return ['dashboard'];
  }

  get prescriptionPatients(): Patient[] {
    if (!this.selectedPrescriptionPatientId) return this.patients;
    return this.patients.filter(patient => patient.id === Number(this.selectedPrescriptionPatientId));
  }

  prescriptionsFor(patient: Patient): any[] {
    return this.prescriptions.filter(item => Number(item.patient) === patient.id);
  }

  addInvoiceItem(): void {
    this.newInvoice.items.push({ service: '', quantity: 1, unit_price: 0 });
  }

  removeInvoiceItem(index: number): void {
    if (this.newInvoice.items.length > 1) this.newInvoice.items.splice(index, 1);
  }

  get invoiceSubtotal(): number {
    return this.newInvoice.items.reduce((sum, item) => sum + Number(item.quantity) * Number(item.unit_price), 0);
  }

  createInvoice(): void {
    const patient = this.patients.find(item => item.id === Number(this.newInvoice.patient));
    const validItems = this.newInvoice.items.filter(item => item.service.trim() && item.quantity > 0 && item.unit_price >= 0);
    if (!patient || !validItems.length) {
      this.showNotice('Choose a patient and add at least one invoice service.', 'error');
      return;
    }
    const request = {
      patient: patient.id,
      patient_name: patient.name,
      invoice_no: `INV-${Date.now().toString().slice(-7)}`,
      discount: Number(this.newInvoice.discount),
      amount: Math.max(this.invoiceSubtotal - Number(this.newInvoice.discount), 0),
      status: 'Pending',
      due_date: this.newInvoice.due_date,
      notes: this.newInvoice.notes,
      items: validItems
    };
    this.http.post<any>(`${this.apiUrl}/bills/`, request).subscribe({
      next: bill => {
        this.bills = [bill, ...this.bills];
        this.showInvoiceForm = false;
        this.newInvoice = {
          patient: 0, discount: 0, due_date: this.todayIso, notes: '',
          items: [{ service: 'Consultation', quantity: 1, unit_price: 0 }]
        };
        this.showNotice(`${bill.invoice_no} was created for ${patient.name}.`, 'success');
      },
      error: error => this.showNotice(error.error?.detail || 'Unable to create the invoice.', 'error')
    });
  }

  addMedicineToPharmacy(): void {
    const form = this.newMedicine;
    if (!form.name.trim() || !form.batch_number.trim() || !form.expiry_date || form.quantity < 0) {
      this.showNotice('Medicine name, batch, quantity and expiry date are required.', 'error');
      return;
    }
    const existing = this.medications.find(item =>
      item.name.toLowerCase() === form.name.trim().toLowerCase() && item.strength === form.strength
    );
    const createStock = (medicationId: number) => {
      this.http.post<any>(`${this.apiUrl}/inventory/`, {
        medication: medicationId,
        batch_number: form.batch_number,
        quantity: Number(form.quantity),
        reorder_level: Number(form.reorder_level),
        unit_cost: Number(form.unit_cost),
        selling_price: Number(form.selling_price),
        expiry_date: form.expiry_date
      }).subscribe({
        next: stock => {
          this.inventory = [...this.inventory, stock];
          this.showMedicineForm = false;
          this.newMedicine = {
            name: '', generic_name: '', form: 'Tablet', strength: '',
            batch_number: '', quantity: 0, reorder_level: 10,
            unit_cost: 0, selling_price: 0, expiry_date: ''
          };
          this.showNotice(`${stock.medication_name} was added to pharmacy stock.`, 'success');
        },
        error: error => this.showNotice(error.error?.non_field_errors?.[0] || 'Unable to add the stock batch.', 'error')
      });
    };
    if (existing) {
      createStock(existing.id);
      return;
    }
    this.http.post<any>(`${this.apiUrl}/medications/`, {
      name: form.name.trim(),
      generic_name: form.generic_name.trim(),
      form: form.form,
      strength: form.strength.trim(),
      active: true
    }).subscribe({
      next: medication => {
        this.medications = [...this.medications, medication];
        createStock(medication.id);
      },
      error: () => this.showNotice('Unable to create the medicine catalogue entry.', 'error')
    });
  }

  get lowStockItems(): any[] {
    return this.inventory.filter(item => item.low_stock);
  }

  addPatient(): void {
    if (!this.newPatient.name.trim() || !this.newPatient.phone.trim() || this.newPatient.age <= 0) {
      this.showNotice('Name, valid age and phone number are required.', 'error');
      return;
    }

    const patientData = { ...this.newPatient };
    this.http.post<Patient>(`${this.apiUrl}/patients/`, patientData).subscribe({
      next: patient => this.finishPatientRegistration(patient),
      error: () => {
        const patient = {
          id: Date.now(),
          patient_id: `PT-${2500 + this.patients.length + 1}`,
          ...patientData
        };
        this.finishPatientRegistration(patient);
      }
    });
  }

  private finishPatientRegistration(patient: Patient): void {
    this.patients = [patient, ...this.patients];
    this.newPatient = {
      name: '', age: 0, gender: 'Female', blood_type: 'A+', phone: '', condition: '',
      email: '', date_of_birth: '', address: '', emergency_contact_name: '',
      emergency_contact_phone: '', allergies: '', medical_history: '', status: 'Active'
    };
    this.showNotice(`${patient.name} was registered as ${patient.patient_id}.`, 'success');
  }

  bookAppointment(): void {
    if (!this.booking.patient_name.trim() || !this.booking.date || !this.booking.time) {
      this.showNotice('Patient name, date and time are required.', 'error');
      return;
    }

    const request = { ...this.booking, status: 'Pending' };
    this.http.post<Appointment>(`${this.apiUrl}/appointments/`, request).subscribe({
      next: appointment => this.finishBooking(appointment),
      error: () => this.finishBooking({ id: Date.now(), ...request })
    });
  }

  private finishBooking(appointment: Appointment): void {
    this.appointments = [appointment, ...this.appointments];
    this.booking = this.emptyBooking();
    this.showNotice(`Appointment requested for ${appointment.patient_name}.`, 'success');
    this.activePage = this.role === 'patient' ? 'patient-booking' : 'appointments';
  }

  updateAppointmentStatus(appointment: Appointment, status: string): void {
    const previousStatus = appointment.status;
    appointment.status = status;
    this.http.patch<Appointment>(`${this.apiUrl}/appointments/${appointment.id}/`, { status }).subscribe({
      next: updated => Object.assign(appointment, updated),
      error: () => {
        if (appointment.id < 100000) appointment.status = previousStatus;
      }
    });
    this.showNotice(`${appointment.patient_name} marked as ${status.toLowerCase()}.`, 'success');
  }

  openConsultation(appointment: Appointment): void {
    const patient = this.patients.find(item =>
      item.patient_id === appointment.patient_code || item.name === appointment.patient_name
    );
    if (patient) this.selectedPatientId = patient.id;
    this.activePage = 'consultation';
  }

  selectPatient(patient: Patient): void {
    this.selectedPatientId = patient.id;
  }

  saveConsultation(): void {
    if (!this.consultation.diagnosis.trim()) {
      this.showNotice('Add a diagnosis before completing the consultation.', 'error');
      return;
    }

    const data = {
      patient_name: this.selectedPatient.name,
      doctor: 'Dr. Sarah Evans',
      ...this.consultation
    };
    this.http.post(`${this.apiUrl}/consultations/`, data).subscribe({
      next: () => this.showNotice('Consultation saved to the patient record.', 'success'),
      error: () => this.showNotice('Consultation saved for this demo session.', 'info')
    });

    const appointment = this.appointments.find(item => item.patient_code === this.selectedPatient.patient_id);
    if (appointment) appointment.status = 'Completed';
  }

  printSummary(): void {
    window.print();
  }

  markBillPaid(bill: Bill): void {
    const previousStatus = bill.status;
    bill.status = 'Paid';
    this.http.patch<Bill>(`${this.apiUrl}/bills/${bill.id}/`, { status: 'Paid' }).subscribe({
      error: () => {
        if (bill.id < 100000) bill.status = previousStatus;
      }
    });
    this.showNotice(`${bill.invoice_no} marked as paid.`, 'success');
  }

  saveSettings(): void {
    this.http.put(`${this.apiUrl}/settings/1/`, this.clinicSettings).subscribe({
      next: () => this.showNotice('Clinic settings saved.', 'success'),
      error: () => this.showNotice('Settings are available for this demo session.', 'info')
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      this.clinicSettings.logo_url = String(reader.result);
    };
    reader.readAsDataURL(file);
  }

  filteredPatients(): Patient[] {
    const query = this.searchText.toLowerCase().trim();
    if (!query) return this.patients;

    return this.patients.filter(patient =>
      [patient.name, patient.patient_id, patient.condition, patient.blood_type, patient.gender, patient.phone, patient.status]
        .some(value => value?.toLowerCase().includes(query)) ||
      patient.age.toString().includes(query)
    );
  }

  filteredAppointments(): Appointment[] {
    const query = this.searchText.toLowerCase().trim();
    if (!query) return this.appointments;

    return this.appointments.filter(appointment =>
      [appointment.patient_name, appointment.patient_code, appointment.doctor, appointment.appointment_type, appointment.status]
        .some(value => value?.toLowerCase().includes(query))
    );
  }

  get selectedPatient(): Patient {
    return this.patients.find(patient => patient.id === this.selectedPatientId) ?? this.patients[0];
  }

  get todaysAppointments(): Appointment[] {
    const dated = this.appointments.filter(appointment => appointment.date === this.todayIso);
    return (dated.length ? dated : this.appointments).slice(0, 6);
  }

  get completedToday(): number {
    return this.todaysAppointments.filter(appointment => appointment.status === 'Completed').length;
  }

  get waitingToday(): number {
    return this.todaysAppointments.filter(appointment =>
      ['Waiting', 'Pending'].includes(appointment.status)
    ).length;
  }

  get confirmedAppointments(): number {
    return this.appointments.filter(appointment => appointment.status === 'Confirmed').length;
  }

  get pendingAppointments(): number {
    return this.appointments.filter(appointment => ['Pending', 'Waiting'].includes(appointment.status)).length;
  }

  get pendingBills(): number {
    return this.bills.filter(bill => bill.status !== 'Paid').length;
  }

  get activePatients(): number {
    return this.patients.filter(patient => patient.status === 'Active').length;
  }

  get averageAge(): number {
    if (!this.patients.length) return 0;
    return Math.round(this.patients.reduce((sum, patient) => sum + Number(patient.age), 0) / this.patients.length);
  }

  get revenue(): number {
    return this.bills
      .filter(bill => bill.status === 'Paid')
      .reduce((sum, bill) => sum + Number(bill.amount), 0);
  }

  get currentPageLabel(): string {
    return this.pageLabels[this.activePage];
  }

  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(amount);
  }

  private emptyBooking() {
    return {
      patient_name: '',
      patient_code: '',
      doctor: 'Dr. Sarah Evans',
      appointment_type: 'General checkup',
      date: this.todayIso,
      time: '09:00 AM',
      notes: ''
    };
  }

  private showNotice(message: string, type: NoticeType): void {
    this.notice = { message, type };
    clearTimeout(this.noticeTimer);
    this.noticeTimer = setTimeout(() => this.notice = null, 3500);
  }
}
