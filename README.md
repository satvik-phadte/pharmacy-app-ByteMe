# Pharmacy App

A Django-based pharmacy management system that connects pharmacies with customers for medicine search and inventory management.
https://pharmacy-app-byteme.onrender.com


## Features

### For Pharmacies:
- **Location Management**: Set pharmacy location with coordinates
-  **Inventory Management**: Add, edit, and delete medicine inventory
-  **Medicine Creation**: Create new medicines on the fly
-  **Dashboard**: View inventory statistics and status
 -  **Alerts**: Low stock and expiry warnings (in dashboard and via optional browser push notifications)

### For Customers:
-  **Location Setting**: Set your location to find nearby pharmacies
-  **Medicine Search**: Search for medicines within a specified distance
-  **Contact Information**: Get pharmacy contact details and directions
-  **Distance Calculation**: See how far each pharmacy is from your location
 -  **Reminders**: Create medicine reminders and get in-app/browser notifications

## Technology Stack

- **Backend**: Django 5.2.5
- **Database**: SQLite (default)
- **Frontend**: HTML, CSS, JavaScript
- **Notifications**: Web Push (django-webpush + Service Worker)
- **Authentication**: Django's built-in authentication system

## Project Structure

```
pharmacy-app/
├── backend/
│   ├── authentication/
│   │   ├── models.py          # Database models
│   │   ├── views.py           # View functions
│   │   ├── forms.py           # Django forms
│   │   ├── urls.py            # URL patterns
│   │   ├── admin.py           # Admin interface
│   │   └── templates/         # HTML templates
│   ├── pharmacy_backend/
│   │   ├── settings.py        # Django settings
│   │   ├── urls.py            # Main URL configuration
│   │   └── wsgi.py            # WSGI configuration
│   └── manage.py              # Django management script
├── frontend/                  # Frontend files (if any)
├── .gitignore                 # Git ignore file
└── README.md                  # This file
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone the Repository
```bash
git clone <your-repository-url>
cd pharmacy-app
```

### Step 2: Set up Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
cd backend
pip install django
pip install django-webpush py-vapid  # for browser push notifications
```

### Step 4: Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

Optional (recommended when using the service worker):
```bash
python manage.py collectstatic --noinput
```

### Step 5: Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### Step 6: Run the Development Server
```bash
python manage.py runserver
```

### Step 7: Access the Application
Open your browser and go to: `http://localhost:8000`

## Usage

### For Pharmacies:
1. **Register/Login**: Create an account with the "Register as Pharmacy" checkbox checked
2. **Set Location**: Go to "Set Pharmacy Location" and enter your coordinates
3. **Manage Inventory**: Add medicines to your inventory with quantities and prices
4. **Monitor**: View your inventory status and statistics on the dashboard
5. **Enable Notifications (optional)**: Toggle browser notifications from the homepage to receive low-stock and expiry alerts

### For Customers:
1. **Register/Login**: Create a regular customer account
2. **Set Location**: Enter your location coordinates
3. **Search Medicines**: Search for specific medicines within your area
4. **Find Pharmacies**: View nearby pharmacies with the medicine you need
5. **Reminders**: Add reminders and (optionally) enable browser notifications from the homepage

## Database Models

### User
- Custom user model extending Django's AbstractUser
- `is_pharmacy` field to distinguish between pharmacy and customer accounts

### PharmacyLocation
- Stores pharmacy location information
- Fields: name, address, latitude, longitude, phone

### Medicine
- Stores medicine information
- Fields: name, generic_name, description, category

### Inventory
- Links pharmacies with medicines
- Fields: pharmacy, medicine, quantity, price, is_available, expiry_date
- Computed flags: low stock (<=5), expiring soon (within 30 days), expired

### CustomerLocation
- Stores customer location for distance calculations
- Fields: user, address, latitude, longitude

### Reminder
- Stores user-configured medicine reminders
- Fields: user, medicine_name, times (comma-separated, 24h), notes, active

### ReminderLog
- Tracks daily adherence for reminders
- Fields: reminder, date, taken, marked_at

## API Endpoints

### Authentication
- `POST /auth/api/login/` - Login API
- `POST /auth/api/signup/` - Registration API

### Web Views
- `GET /auth/login/` - Login page
- `GET /auth/signup/` - Registration page
- `GET /auth/homepage/` - Main dashboard
- `GET /auth/pharmacy/location/` - Pharmacy location management
- `GET /auth/pharmacy/inventory/` - Inventory management
- `GET /auth/customer/location/` - Customer location setting
- `GET /auth/customer/search/` - Medicine search
- `POST /auth/send-test-notification/` - Send a test push notification to current user (after enabling notifications)

## Features in Detail

### Distance Calculation
The app uses the Haversine formula to calculate distances between customer and pharmacy locations, providing accurate distance information for medicine searches.

### Inventory Management
- Add new medicines with automatic creation in the database
- Track quantities, prices, and expiry dates
- Set availability status
- View low stock warnings and expiry alerts

### Search Functionality
- Search by medicine name
- Filter by maximum distance
- Display pharmacy contact information
- Provide directions via Google Maps
- Hide expiry info in customer search results for a cleaner UX

### Reminders & Notifications
- Create/manage reminders with multiple times per day
- Mark as taken (per day)
- Optional browser push notifications (desktop/mobile) for:
   - Customer reminders
   - Pharmacy low-stock and expiry alerts

## Browser Push Notifications (Web Push)

Browser notifications are implemented using Service Workers and django-webpush. In development they work on http://127.0.0.1, and in production require HTTPS.

### 1) Dependencies
```bash
pip install django-webpush py-vapid
```

### 2) Generate VAPID Keys
We include a helper script:
```bash
cd backend
python generate_vapid_keys.py
```
Copy the printed VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY to your environment (recommended) or settings for a quick start.

### 3) Configure Django
- In `pharmacy_backend/settings.py`:
   - Add to INSTALLED_APPS: `webpush`
   - Add WEBPUSH_SETTINGS (use env in production):
      ```python
      WEBPUSH_SETTINGS = {
            "VAPID_PUBLIC_KEY": "<public>",
            "VAPID_PRIVATE_KEY": "<private>",
            "VAPID_ADMIN_EMAIL": "mailto:admin@pharmacy-app.com",
      }
      ```
- In `pharmacy_backend/urls.py` add:
   ```python
   path('webpush/', include('webpush.urls')),
   ```
- Static for service worker:
   ```python
   STATIC_URL = 'static/'
   STATIC_ROOT = BASE_DIR / 'staticfiles'
   ```

### 4) Migrations & static
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 5) Try it
- Open `/auth/homepage/`
- Click Enable (allow browser permission)
- Click Test to receive a notification

### Notes
- Use environment variables for VAPID keys in production (do not commit private keys)
- Service workers require HTTPS in production

## Security Features

- Django's built-in CSRF protection
- User authentication and authorization
- Form validation and sanitization
- Secure password handling

## Customization

### Adding New Features
1. Create new models in `authentication/models.py`
2. Add corresponding forms in `authentication/forms.py`
3. Create views in `authentication/views.py`
4. Add URL patterns in `authentication/urls.py`
5. Create templates in `authentication/templates/`

### Styling
The app uses custom CSS for a modern, responsive design. Styles are defined in the base template and can be customized as needed.

## Troubleshooting

### Common Issues

1. **Database Migration Errors**
   ```bash
   python manage.py makemigrations --empty authentication
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Static Files Not Loading**
   - Ensure `django.contrib.staticfiles` is in `INSTALLED_APPS`
   - Run `python manage.py collectstatic` if needed
   - Ensure `STATIC_ROOT` is set in settings if you use `collectstatic`

3. **Permission Errors**
   - Make sure you're logged in as a pharmacy user for pharmacy features
   - Check user permissions in Django admin

4. **Push Notifications Not Working**
   - Verify browser permission is granted
   - Ensure service worker is registered (DevTools > Application)
   - Confirm VAPID keys are set and valid
   - For production, ensure the site runs over HTTPS

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

For support or questions, please open an issue in the GitHub repository.
