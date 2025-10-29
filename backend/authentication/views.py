from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from webpush import send_user_notification
from .forms import (
    UserRegistrationForm, UserLoginForm, PharmacyLocationForm, 
    MedicineForm, InventoryForm, CustomerLocationForm, MedicineSearchForm,
    BulkMedicineUploadForm, ReminderForm, PrescriptionUploadForm
)
from .models import User, PharmacyLocation, Medicine, Inventory, CustomerLocation, Reminder, ReminderLog, Prescription
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
    from django.conf import settings
    
    context = {
        'user': request.user,
        'is_pharmacy': request.user.is_pharmacy,
        'WEBPUSH_SETTINGS': settings.WEBPUSH_SETTINGS
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

        # Load active reminders for overlay
        reminders = Reminder.objects.filter(user=request.user, active=True).order_by('medicine_name')
        # Build 'taken today' map
        from datetime import date
        today = date.today()
        taken_ids = [log.reminder_id for log in ReminderLog.objects.filter(reminder__in=reminders, date=today, taken=True)]
        context['reminders'] = reminders
        context['reminders_taken_today_ids'] = taken_ids

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

    # Gather low stock and expiry warnings
    low_stock_items = [item for item in inventory_items if item.is_low_stock]
    expiring_soon_items = [item for item in inventory_items if item.is_expiring_soon and not item.is_expired]
    expired_items = [item for item in inventory_items if item.is_expired]

    return render(request, 'authentication/inventory_list.html', {
        'inventory_items': inventory_items,
        'low_stock_items': low_stock_items,
        'expiring_soon_items': expiring_soon_items,
        'expired_items': expired_items,
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


# --- Reminders ---
@login_required
def reminders_view(request):
    if request.user.is_pharmacy:
        messages.error(request, 'This feature is for customers only.')
        return redirect('authentication:homepage')

    if request.method == 'POST':
        form = ReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.user = request.user
            reminder.save()
            messages.success(request, 'Reminder added!')
            return redirect('authentication:reminders')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReminderForm()

    reminders = Reminder.objects.filter(user=request.user).order_by('-active', 'medicine_name')
    return render(request, 'authentication/reminders.html', {
        'form': form,
        'reminders': reminders,
    })


@login_required
def reminder_mark_taken_today(request, pk):
    if request.user.is_pharmacy:
        return JsonResponse({'success': False, 'message': 'Not allowed'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    reminder = get_object_or_404(Reminder, pk=pk, user=request.user)
    from datetime import date
    today = date.today()
    log, _ = ReminderLog.objects.get_or_create(reminder=reminder, date=today)
    log.taken = True
    log.save()
    return JsonResponse({'success': True})


@login_required
def reminder_delete_view(request, pk):
    """Delete a reminder owned by the current (non-pharmacy) user."""
    if request.user.is_pharmacy:
        messages.error(request, 'This feature is for customers only.')
        return redirect('authentication:homepage')

    reminder = get_object_or_404(Reminder, pk=pk, user=request.user)
    if request.method == 'POST':
        reminder.delete()
        messages.success(request, 'Reminder deleted.')
        return redirect('authentication:reminders')

    # For non-POST, just redirect back to reminders (avoid accidental deletions via GET)
    messages.info(request, 'Deletion cancelled.')
    return redirect('authentication:reminders')


# --- Prescription Upload Views ---
@login_required
def prescriptions_view(request):
    """View and upload prescriptions for regular users"""
    if request.user.is_pharmacy:
        messages.error(request, 'This feature is for customers only.')
        return redirect('authentication:homepage')
    
    if request.method == 'POST':
        form = PrescriptionUploadForm(request.POST, request.FILES)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.user = request.user
            prescription.save()
            messages.success(request, 'Prescription uploaded successfully!')
            return redirect('authentication:prescriptions')
    else:
        form = PrescriptionUploadForm()
    
    prescriptions = Prescription.objects.filter(user=request.user)
    
    context = {
        'form': form,
        'prescriptions': prescriptions,
    }
    return render(request, 'authentication/prescriptions.html', context)


@login_required
def prescription_delete_view(request, pk):
    """Delete a prescription owned by the current user"""
    if request.user.is_pharmacy:
        messages.error(request, 'This feature is for customers only.')
        return redirect('authentication:homepage')
    
    prescription = get_object_or_404(Prescription, pk=pk, user=request.user)
    if request.method == 'POST':
        prescription.image.delete()  # Delete the image file
        prescription.delete()
        messages.success(request, 'Prescription deleted successfully.')
        return redirect('authentication:prescriptions')
    
    messages.info(request, 'Deletion cancelled.')
    return redirect('authentication:prescriptions')


@login_required
def prescription_extract_text_view(request, pk):
    """Extract text from prescription image using Google Gemini OCR"""
    if request.user.is_pharmacy:
        return JsonResponse({'success': False, 'error': 'This feature is for customers only.'})
    
    prescription = get_object_or_404(Prescription, pk=pk, user=request.user)
    
    try:
        import google.generativeai as genai
        from django.conf import settings
        from PIL import Image
        
        # Configure Gemini API
        if not settings.GEMINI_API_KEY:
            return JsonResponse({'success': False, 'error': 'Gemini API key not configured. Please add your API key to settings.py'})
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Get the image file path and open it
        image_path = prescription.image.path
        img = Image.open(image_path)
        
        # Create model - using gemini-pro-vision or gemini-1.5-pro
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = """
        Extract all text from this medical prescription image. 
        Please provide:
        1. Medicine names
        2. Dosages
        3. Instructions for use
        4. Duration
        5. Doctor's name (if visible)
        6. Any other important information
        
        Format the output clearly with proper labels.
        """
        
        response = model.generate_content([prompt, img])
        extracted_text = response.text
        
        # Save extracted text to database
        prescription.extracted_text = extracted_text
        prescription.save()
        
        return JsonResponse({'success': True, 'extracted_text': extracted_text})
        
    except ImportError as ie:
        missing_package = str(ie).split("'")[1] if "'" in str(ie) else "required package"
        return JsonResponse({'success': False, 'error': f'{missing_package} not installed. Run: pip install {missing_package}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error extracting text: {str(e)}'})



# --- Push Notification Helpers ---
def send_push_notification(user, title, body, url='/'):
    """Helper function to send push notification to a user"""
    try:
        payload = {
            'head': title,
            'body': body,
            'icon': '/static/authentication/icon.png',
            'url': url
        }
        send_user_notification(user=user, payload=payload, ttl=1000)
        return True
    except Exception as e:
        print(f'Failed to send notification to {user.username}: {e}')
        return False


@login_required
def send_test_notification(request):
    """Send a test notification to the current user"""
    if request.method == 'POST':
        success = send_push_notification(
            user=request.user,
            title='Test Notification',
            body='This is a test notification from Pharmacy App!',
            url='/auth/homepage/'
        )
        if success:
            return JsonResponse({'success': True, 'message': 'Test notification sent!'})
        else:
            return JsonResponse({'success': False, 'message': 'Failed to send notification'}, status=500)
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)


def notify_low_stock_items(pharmacy_user):
    """Send notification for low stock items to pharmacy"""
    inventory_items = Inventory.objects.filter(pharmacy=pharmacy_user)
    low_stock_items = [item for item in inventory_items if item.is_low_stock]
    
    if low_stock_items:
        item_names = ', '.join([item.medicine.name for item in low_stock_items[:3]])
        more = f' and {len(low_stock_items) - 3} more' if len(low_stock_items) > 3 else ''
        
        send_push_notification(
            user=pharmacy_user,
            title='⚠️ Low Stock Alert',
            body=f'Low stock: {item_names}{more}',
            url='/auth/pharmacy/inventory/'
        )


def notify_expiring_items(pharmacy_user):
    """Send notification for expiring items to pharmacy"""
    inventory_items = Inventory.objects.filter(pharmacy=pharmacy_user)
    expiring_items = [item for item in inventory_items if item.is_expiring_soon and not item.is_expired]
    
    if expiring_items:
        item_names = ', '.join([item.medicine.name for item in expiring_items[:3]])
        more = f' and {len(expiring_items) - 3} more' if len(expiring_items) > 3 else ''
        
        send_push_notification(
            user=pharmacy_user,
            title='⏰ Expiry Warning',
            body=f'Expiring soon: {item_names}{more}',
            url='/auth/pharmacy/inventory/'
        )


def notify_medicine_reminder(user, reminder):
    """Send notification for medicine reminder to customer"""
    send_push_notification(
        user=user,
        title=f'💊 Medicine Reminder',
        body=f'Time to take your medicine: {reminder.medicine_name}',
        url='/auth/homepage/'
    )
