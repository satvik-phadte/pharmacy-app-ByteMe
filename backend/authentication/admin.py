from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PharmacyLocation, Medicine, Inventory, CustomerLocation

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_pharmacy', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_pharmacy', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Pharmacy Settings', {'fields': ('is_pharmacy',)}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Pharmacy Settings', {'fields': ('is_pharmacy',)}),
    )

@admin.register(PharmacyLocation)
class PharmacyLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'address', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'user__username', 'address')
    ordering = ('-created_at',)

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'generic_name', 'description')
    ordering = ('name',)

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'pharmacy', 'quantity', 'price', 'is_available', 'expiry_date')
    list_filter = ('is_available', 'expiry_date', 'created_at')
    search_fields = ('medicine__name', 'pharmacy__username')
    ordering = ('-created_at',)

@admin.register(CustomerLocation)
class CustomerLocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'created_at')
    search_fields = ('user__username', 'address')
    ordering = ('-created_at',)
