from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    is_pharmacy = models.BooleanField(default=False, verbose_name="Pharmacy Account")
    
    def __str__(self):
        return self.username

class PharmacyLocation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pharmacy_location')
    name = models.CharField(max_length=200, help_text="Pharmacy name")
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.address}"

class Medicine(models.Model):
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ['name', 'generic_name']

class Inventory(models.Model):
    pharmacy = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.medicine.name} - {self.pharmacy.username} - Qty: {self.quantity}"
    
    class Meta:
        unique_together = ['pharmacy', 'medicine']

class CustomerLocation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_location')
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.address}"

# --- Reminders for regular users ---
class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    medicine_name = models.CharField(max_length=200)
    times = models.CharField(
        max_length=200,
        help_text="Comma-separated times in 24h format, e.g. 08:00, 20:00"
    )
    notes = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.medicine_name} ({self.user.username})"

class ReminderLog(models.Model):
    reminder = models.ForeignKey(Reminder, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField()
    taken = models.BooleanField(default=False)
    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('reminder', 'date')

    def __str__(self):
        return f"{self.reminder.medicine_name} - {self.date} - {'taken' if self.taken else 'pending'}"
