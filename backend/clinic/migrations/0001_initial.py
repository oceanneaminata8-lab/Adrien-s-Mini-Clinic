from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient_name', models.CharField(max_length=120)),
                ('patient_code', models.CharField(blank=True, max_length=20)),
                ('doctor', models.CharField(max_length=120)),
                ('appointment_type', models.CharField(max_length=80)),
                ('date', models.DateField()),
                ('time', models.CharField(max_length=20)),
                ('status', models.CharField(default='Pending', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient_name', models.CharField(max_length=120)),
                ('invoice_no', models.CharField(max_length=30, unique=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(default='Pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Consultation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient_name', models.CharField(max_length=120)),
                ('doctor', models.CharField(max_length=120)),
                ('symptoms', models.TextField(blank=True)),
                ('diagnosis', models.TextField()),
                ('treatment_notes', models.TextField(blank=True)),
                ('prescription', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient_id', models.CharField(blank=True, max_length=20, unique=True)),
                ('name', models.CharField(max_length=120)),
                ('age', models.PositiveIntegerField(default=0)),
                ('gender', models.CharField(max_length=20)),
                ('blood_type', models.CharField(blank=True, max_length=5)),
                ('phone', models.CharField(max_length=30)),
                ('condition', models.CharField(blank=True, max_length=120)),
                ('status', models.CharField(default='Active', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
