from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .forms import (
    UserRegistrationForm, UserLoginForm, PharmacyLocationForm, 
    MedicineForm, InventoryForm, CustomerLocationForm, MedicineSearchForm,
    BulkMedicineUploadForm
)
from .models import User, PharmacyLocation, Medicine, Inventory, CustomerLocation
import math

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('authentication:homepage')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created successfully for {user.username}!')
            return redirect('authentication:homepage')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'authentication/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('authentication:homepage')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('authentication:homepage')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'authentication/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('authentication:login')

@login_required
def homepage_view(request):
    context = {
        'user': request.user,
        'is_pharmacy': request.user.is_pharmacy
    }
    
    if request.user.is_pharmacy:
        # Get pharmacy location and inventory
        try:
            pharmacy_location = request.user.pharmacy_location
            context['pharmacy_location'] = pharmacy_location
        except PharmacyLocation.DoesNotExist:
            context['pharmacy_location'] = None
            
        inventory_items = Inventory.objects.filter(pharmacy=request.user)
        context['inventory_items'] = inventory_items
        context['total_items'] = inventory_items.count()
        context['available_items'] = inventory_items.filter(is_available=True).count()
    else:
        # Get customer location
        try:
            customer_location = request.user.customer_location
            context['customer_location'] = customer_location
        except CustomerLocation.DoesNotExist:
            context['customer_location'] = None
    
    return render(request, 'authentication/homepage.html', context)

# Pharmacy Location Management
@login_required
def pharmacy_location_view(request):
    if not request.user.is_pharmacy:
        messages.error(request, 'Access denied. Pharmacy account required.')
        return redirect('authentication:homepage')
    
    try:
        location = request.user.pharmacy_location
    except PharmacyLocation.DoesNotExist:
        location = None
    
    if request.method == 'POST':
        form = PharmacyLocationForm(request.POST, instance=location)
        if form.is_valid():
            location = form.save(commit=False)
            location.user = request.user
            location.save()
            messages.success(request, 'Pharmacy location updated successfully!')
            return redirect('authentication:pharmacy_location')
    else:
        form = PharmacyLocationForm(instance=location)
    
    return render(request, 'authentication/pharmacy_location.html', {
        'form': form,
        'location': location
    })

# Inventory Management
@login_required
def inventory_list_view(request):
    if not request.user.is_pharmacy:
        messages.error(request, 'Access denied. Pharmacy account required.')
        return redirect('authentication:homepage')
    
    inventory_items = Inventory.objects.filter(pharmacy=request.user).select_related('medicine')
    
    return render(request, 'authentication/inventory_list.html', {
        'inventory_items': inventory_items
    })

@login_required
def inventory_add_view(request):
    if not request.user.is_pharmacy:
        messages.error(request, 'Access denied. Pharmacy account required.')
        return redirect('authentication:homepage')
    
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            # Check if we need to create a new medicine
            new_medicine_name = form.cleaned_data.get('new_medicine_name')
            new_medicine_generic = form.cleaned_data.get('new_medicine_generic')
            
            if new_medicine_name:
                # Create new medicine
                medicine, created = Medicine.objects.get_or_create(
                    name=new_medicine_name,
                    defaults={
                        'generic_name': new_medicine_generic or '',
                        'description': f'Medicine added by {request.user.username}',
                        'category': 'General'
                    }
                )
                if created:
                    messages.success(request, f'New medicine "{new_medicine_name}" created successfully!')
            else:
                # Use existing medicine
                medicine = form.cleaned_data.get('medicine')
                if not medicine:
                    messages.error(request, 'Please select an existing medicine or enter a new medicine name.')
                    return render(request, 'authentication/inventory_form.html', {
                        'form': form,
                        'title': 'Add Inventory Item'
                    })
            
            # Create inventory item
            inventory = form.save(commit=False)
            inventory.pharmacy = request.user
            inventory.medicine = medicine
            inventory.save()
            messages.success(request, 'Inventory item added successfully!')
            return redirect('authentication:inventory_list')
    else:
        form = InventoryForm()
    
    return render(request, 'authentication/inventory_form.html', {
        'form': form,
        'title': 'Add Inventory Item'
    })

@login_required
def inventory_edit_view(request, pk):
    if not request.user.is_pharmacy:
        messages.error(request, 'Access denied. Pharmacy account required.')
        return redirect('authentication:homepage')
    
    inventory_item = get_object_or_404(Inventory, pk=pk, pharmacy=request.user)
    
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=inventory_item)
        if form.is_valid():
            # For editing, we'll use the existing medicine
            form.save()
            messages.success(request, 'Inventory item updated successfully!')
            return redirect('authentication:inventory_list')
    else:
        form = InventoryForm(instance=inventory_item)
    
    return render(request, 'authentication/inventory_form.html', {
        'form': form,
        'title': 'Edit Inventory Item',
        'inventory_item': inventory_item
    })

@login_required
def inventory_delete_view(request, pk):
    if not request.user.is_pharmacy:
        messages.error(request, 'Access denied. Pharmacy account required.')
        return redirect('authentication:homepage')
    
    inventory_item = get_object_or_404(Inventory, pk=pk, pharmacy=request.user)
    
    if request.method == 'POST':
        inventory_item.delete()
        messages.success(request, 'Inventory item deleted successfully!')
        return redirect('authentication:inventory_list')
    
    return render(request, 'authentication/inventory_confirm_delete.html', {
        'inventory_item': inventory_item
    })

# Customer Location Management
@login_required
def customer_location_view(request):
    if request.user.is_pharmacy:
        messages.error(request, 'This feature is for customers only.')
        return redirect('authentication:homepage')
    
    try:
        location = request.user.customer_location
    except CustomerLocation.DoesNotExist:
        location = None
    
    if request.method == 'POST':
        form = CustomerLocationForm(request.POST, instance=location)
        if form.is_valid():
            location = form.save(commit=False)
            location.user = request.user
            location.save()
            messages.success(request, 'Location updated successfully!')
            return redirect('authentication:customer_location')
    else:
        form = CustomerLocationForm(instance=location)
    
    return render(request, 'authentication/customer_location.html', {
        'form': form,
        'location': location
    })

# Medicine Search
@login_required
def medicine_search_view(request):
    if request.user.is_pharmacy:
        messages.error(request, 'This feature is for customers only.')
        return redirect('authentication:homepage')
    
    search_results = []
    form = MedicineSearchForm(request.GET or None)
    
    if form.is_valid():
        medicine_name = form.cleaned_data['medicine_name']
        max_distance = form.cleaned_data['max_distance']
        
        # Get customer location
        try:
            customer_location = request.user.customer_location
            if customer_location:
                # Search for medicine in nearby pharmacies
                search_results = search_medicine_nearby(
                    medicine_name, 
                    customer_location.latitude, 
                    customer_location.longitude, 
                    max_distance
                )
            else:
                messages.warning(request, 'Please set your location first to search for medicines.')
        except CustomerLocation.DoesNotExist:
            messages.warning(request, 'Please set your location first to search for medicines.')
    
    return render(request, 'authentication/medicine_search.html', {
        'form': form,
        'search_results': search_results
    })

def search_medicine_nearby(medicine_name, lat, lng, max_distance):
    """Search for medicine in nearby pharmacies"""
    # Simple distance calculation (Haversine formula)
    def calculate_distance(lat1, lng1, lat2, lng2):
        R = 6371  # Earth's radius in kilometers
        
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    # Search for medicine
    medicine_query = Q(name__icontains=medicine_name) | Q(generic_name__icontains=medicine_name)
    medicines = Medicine.objects.filter(medicine_query)
    
    results = []
    for medicine in medicines:
        # Find pharmacies with this medicine
        inventory_items = Inventory.objects.filter(
            medicine=medicine,
            is_available=True,
            quantity__gt=0
        ).select_related('pharmacy', 'pharmacy__pharmacy_location')
        
        for item in inventory_items:
            try:
                pharmacy_location = item.pharmacy.pharmacy_location
                if pharmacy_location and pharmacy_location.is_active:
                    distance = calculate_distance(
                        lat, lng, 
                        float(pharmacy_location.latitude), 
                        float(pharmacy_location.longitude)
                    )
                    
                    if distance <= max_distance:
                        results.append({
                            'pharmacy': item.pharmacy,
                            'pharmacy_location': pharmacy_location,
                            'medicine': medicine,
                            'inventory_item': item,
                            'distance': round(distance, 2)
                        })
            except PharmacyLocation.DoesNotExist:
                continue
    
    # Sort by distance
    results.sort(key=lambda x: x['distance'])
    return results

# API endpoints
def api_login(request):
    """API endpoint for login (no CORS)"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'username': user.username,
                        'is_pharmacy': user.is_pharmacy
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid credentials'
                }, status=400)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Username and password required'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

def api_signup(request):
    """API endpoint for signup (no CORS)"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        is_pharmacy = request.POST.get('is_pharmacy') == 'true'
        
        if not all([username, password1, password2]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required'
            }, status=400)
        
        if password1 != password2:
            return JsonResponse({
                'success': False,
                'message': 'Passwords do not match'
            }, status=400)
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'message': 'Username already exists'
            }, status=400)
        
        try:
            user = User.objects.create_user(
                username=username,
                password=password1,
                is_pharmacy=is_pharmacy
            )
            login(request, user)
            return JsonResponse({
                'success': True,
                'message': 'Account created successfully',
                'user': {
                    'username': user.username,
                    'is_pharmacy': user.is_pharmacy
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@login_required
def bulk_medicine_upload_view(request):
    """View for bulk uploading medicines via Excel file"""
    if not request.user.is_pharmacy:
        messages.error(request, 'Access denied. Pharmacy account required.')
        return redirect('authentication:homepage')
    
    if request.method == 'POST':
        form = BulkMedicineUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = form.cleaned_data['excel_file']
            
            try:
                # Import pandas and openpyxl for Excel processing
                import pandas as pd
                
                # Read Excel file
                df = pd.read_excel(excel_file)
                
                # Validate required columns
                required_columns = ['medicine_name', 'quantity', 'price']
                optional_columns = ['generic_name', 'description', 'category', 'expiry_date', 'is_available']
                
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    messages.error(request, f'Missing required columns: {", ".join(missing_columns)}')
                    return render(request, 'authentication/bulk_medicine_upload.html', {'form': form})
                
                # Process each row
                created_medicines = 0
                created_inventory = 0
                errors = []
                
                for index, row in df.iterrows():
                    try:
                        # Create or get medicine
                        medicine_name = str(row['medicine_name']).strip()
                        generic_name = str(row.get('generic_name', '')).strip() if pd.notna(row.get('generic_name')) else ''
                        description = str(row.get('description', '')).strip() if pd.notna(row.get('description')) else ''
                        category = str(row.get('category', 'General')).strip() if pd.notna(row.get('category')) else 'General'
                        
                        if not medicine_name or medicine_name.lower() == 'nan':
                            errors.append(f'Row {index + 2}: Medicine name is required')
                            continue
                        
                        medicine, medicine_created = Medicine.objects.get_or_create(
                            name=medicine_name,
                            defaults={
                                'generic_name': generic_name,
                                'description': description,
                                'category': category
                            }
                        )
                        
                        if medicine_created:
                            created_medicines += 1
                        
                        # Create or update inventory
                        quantity = int(row['quantity']) if pd.notna(row['quantity']) else 0
                        price = float(row['price']) if pd.notna(row['price']) else 0.0
                        is_available = bool(row.get('is_available', True)) if pd.notna(row.get('is_available')) else True
                        expiry_date = pd.to_datetime(row['expiry_date']).date() if pd.notna(row.get('expiry_date')) else None
                        
                        if quantity < 0:
                            errors.append(f'Row {index + 2}: Quantity cannot be negative')
                            continue
                        
                        if price < 0:
                            errors.append(f'Row {index + 2}: Price cannot be negative')
                            continue
                        
                        inventory, inventory_created = Inventory.objects.update_or_create(
                            pharmacy=request.user,
                            medicine=medicine,
                            defaults={
                                'quantity': quantity,
                                'price': price,
                                'is_available': is_available,
                                'expiry_date': expiry_date
                            }
                        )
                        
                        if inventory_created:
                            created_inventory += 1
                    
                    except Exception as e:
                        errors.append(f'Row {index + 2}: {str(e)}')
                        continue
                
                # Show results
                success_msg = f'Successfully processed: {created_medicines} new medicines, {created_inventory} inventory items'
                messages.success(request, success_msg)
                
                if errors:
                    error_msg = f'{len(errors)} errors occurred: ' + '; '.join(errors[:5])
                    if len(errors) > 5:
                        error_msg += f' and {len(errors) - 5} more...'
                    messages.warning(request, error_msg)
                
                return redirect('authentication:inventory_list')
                
            except ImportError:
                messages.error(request, 'Excel processing libraries not installed. Please install pandas and openpyxl.')
                return render(request, 'authentication/bulk_medicine_upload.html', {'form': form})
            
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
                return render(request, 'authentication/bulk_medicine_upload.html', {'form': form})
    else:
        form = BulkMedicineUploadForm()
    
    return render(request, 'authentication/bulk_medicine_upload.html', {'form': form})
