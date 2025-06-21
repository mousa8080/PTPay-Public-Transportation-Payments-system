# ===== File: payments/models.py =====

from django.db import models
from decimal import Decimal
from django.contrib.auth.hashers import make_password, identify_hasher
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils.crypto import get_random_string
from django.db.models.signals import post_save, pre_save
from django.db.models import Q, UniqueConstraint
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Governorate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class City(models.Model):
    name        = models.CharField(max_length=100)
    governorate = models.ForeignKey(Governorate, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return f"{self.name} ({self.governorate.name if self.governorate else '-'})"

class Device(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return f"Device {self.id}: {self.name}"

class DeviceLocation(models.Model):
    device    = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='locations')
    latitude  = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-timestamp']
    def __str__(self):
        return f"Loc {self.id} of Device {self.device.id} at {self.timestamp}"

class Customer(models.Model):
    name        = models.CharField(max_length=100)
    uid         = models.CharField(max_length=100, unique=True, blank=True, null=True)
    national_id = models.CharField(max_length=14, unique=True,
        validators=[MinLengthValidator(14), RegexValidator(r'^\d{14}$')])
    phone       = models.CharField(max_length=11, unique=True,
        validators=[MinLengthValidator(11), RegexValidator(r'^\d{11}$')])
    email       = models.EmailField(unique=True,
        validators=[RegexValidator(r'^[\w.+-]+@gmail\.com$')])
    password    = models.CharField(max_length=128, validators=[MinLengthValidator(8)])
    governorate = models.ForeignKey(Governorate, on_delete=models.SET_NULL, null=True, blank=True)
    city        = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    is_active   = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        raw = self.password or ""
        try:
            identify_hasher(raw)
        except:
            self.password = make_password(raw)
        if not self.uid:
            self.uid = get_random_string(10)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.national_id})"

class Driver(models.Model):
    uid = models.CharField(max_length=100, unique=True, blank=True, null=True)

    @property
    def is_authenticated(self):
        return True

    name = models.CharField(max_length=100)

    national_id = models.CharField(
        max_length=14,
        unique=True,
        validators=[
            MinLengthValidator(14),
            RegexValidator(r'^\d{14}$')
        ]
    )

    phone = models.CharField(
        max_length=11,
        unique=True,
        validators=[
            MinLengthValidator(11),
            RegexValidator(r'^\d{11}$')
        ]
    )

    email = models.EmailField(
        unique=True,
        validators=[
            RegexValidator(r'^[\w.+-]+@gmail\.com$')
        ]
    )

    password = models.CharField(
        max_length=128,
        validators=[MinLengthValidator(8)]
    )

    license_number = models.CharField(max_length=50, unique=True)

    driver_photo = models.ImageField(
        upload_to='drivers/photos/', null=True, blank=True
    )

    license_photo = models.ImageField(
        upload_to='drivers/licenses/', null=True, blank=True
    )

    governorate = models.ForeignKey(
        'Governorate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    city = models.ForeignKey(
        'City',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    in_zone = models.BooleanField(default=False)

    assigned_device = models.OneToOneField(
        'Device',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='driver'
    )

    assigned_route = models.ForeignKey(
        'Route',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drivers'
    )

    def save(self, *args, **kwargs):
        # توليد uid تلقائيًا إذا مش موجود
        if not self.uid:
            self.uid = get_random_string(12)  # 12 حرف عشوائي
        # تشفير الباسورد إذا لم يكن مشفر
        raw = self.password or ""
        try:
            identify_hasher(raw)
        except:
            self.password = make_password(raw)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.national_id})"


class CustomerWallet(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='wallet')
    balance  = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    def __str__(self): return f"Wallet of {self.customer.name}"

class DriverWallet(models.Model):
    driver          = models.OneToOneField(Driver, on_delete=models.CASCADE, related_name='wallet')
    balance         = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"Wallet of {self.driver.name}"


@receiver(post_save, sender=Customer)
def create_customer_wallet(sender, instance, created, **kwargs):
    if created: CustomerWallet.objects.create(customer=instance)

@receiver(post_save, sender=Driver)
def create_driver_wallet(sender, instance, created, **kwargs):
    if created: DriverWallet.objects.create(driver=instance)




class Route(models.Model):
    # حدفنا حقل name الأصلي من هنا
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='routes')
    # … لا حاجة للحقول الستّة القديمة start_/end_…

    @property
    def display_name(self):
        names = [stop.name for stop in self.stops.all()]
        return " - ".join(names)

    def __str__(self):
        return self.display_name  # يظهر في الـ Admin وغيره تلقائيّاً




class Vehicle(models.Model):
    number = models.CharField(max_length=50, unique=True)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='vehicles')
    def __str__(self): return f"{self.number} - {self.driver.name}"





from django.db import models
from django.utils import timezone
from django.db.models import Q, UniqueConstraint
from django.utils.crypto import get_random_string

class Trip(models.Model):
    driver          = models.ForeignKey('Driver', on_delete=models.CASCADE, related_name='trips')
    vehicle         = models.ForeignKey('Vehicle', on_delete=models.CASCADE, related_name='trips')
    route           = models.ForeignKey('Route', on_delete=models.CASCADE, related_name='trips')
    date            = models.DateField(auto_now_add=True)
    sequence_number = models.PositiveIntegerField()
    start_time      = models.DateTimeField(null=True, blank=True)  # تم تعديل هذا السطر
    end_time        = models.DateTimeField(null=True, blank=True)
    in_zone         = models.BooleanField(default=False)
    qr_token               = models.CharField(max_length=32, blank=True)
    qr_token_generated_at  = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Trip {self.sequence_number} by {self.driver.name}"

    def get_qr_token(self):
        now = timezone.now()
        if not self.qr_token_generated_at or (now - self.qr_token_generated_at).total_seconds() >= 10:
            token = get_random_string(32)
            self.qr_token = token
            self.qr_token_generated_at = now
            self.save(update_fields=['qr_token', 'qr_token_generated_at'])
        return self.qr_token

    def start_trip(self):
        self.start_time = timezone.now()
        self.save(update_fields=['start_time'])

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['vehicle'],
                condition=Q(end_time__isnull=True),
                name='unique_active_trip_per_vehicle'
            ),
        ]




class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('nfc','NFC Card'),('qr','QR'),('cash','Cash'),('unk','Unknown'),
    )
    customer       = models.ForeignKey(Customer, on_delete=models.CASCADE)
    trip           = models.ForeignKey(Trip, on_delete=models.CASCADE, null=True, blank=True)
    fare           = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    new_balance    = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    timestamp      = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=4, choices=PAYMENT_METHOD_CHOICES, default='unk')
    def __str__(self): return f"Payment {self.id} for {self.customer.name}"

class NFCCard(models.Model):
    uid      = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='nfc_cards')
    def __str__(self): return f"NFC {self.uid} for {self.customer.name}"

class Transfer(models.Model):
    sender_phone = models.CharField(max_length=11, validators=[MinLengthValidator(11), RegexValidator(r'^\d{11}$')])
    receiver_phone = models.CharField(max_length=11, validators=[MinLengthValidator(11), RegexValidator(r'^\d{11}$')])
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transfer {self.id}: {self.amount} from {self.sender_phone} to {self.receiver_phone}"



@receiver(pre_save, sender=Driver)
def _cache_old_in_zone(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Driver.objects.get(pk=instance.pk)
            instance._old_in_zone = old.in_zone
        except Driver.DoesNotExist:
            instance._old_in_zone = False

@receiver(post_save, sender=Driver)
def _on_in_zone_changed(sender, instance, created, **kwargs):
    if created or not hasattr(instance, '_old_in_zone'):
        return

    was_in = instance._old_in_zone
    now_in = instance.in_zone
    if not was_in and now_in:
        # طباعة للتتبع (اختياري)
        print(f"[signal] Driver {instance.id} دخل in_zone – سيُنهى Trip ويرحّل الرصيد.")

        try:
            trip = Trip.objects.filter(
                driver=instance, end_time__isnull=True
            ).latest('start_time')
            trip.end_time = timezone.now()
            trip.in_zone  = True
            trip.save(update_fields=['end_time', 'in_zone'])
        except Trip.DoesNotExist:
            return

        try:
            dw = DriverWallet.objects.get(driver=instance)
            dw.balance         += dw.pending_balance
            dw.pending_balance  = Decimal('0.00')
            dw.save(update_fields=['balance', 'pending_balance'])
        except DriverWallet.DoesNotExist:
            pass



# payments/models.py

class Stop(models.Model):
    route   = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='stops'
    )
    name    = models.CharField(max_length=100)
    min_lat = models.FloatField()
    min_lng = models.FloatField()
    max_lat = models.FloatField()
    max_lng = models.FloatField()

    def __str__(self):
        return self.name











