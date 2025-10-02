# Pharmacy App

A Django-based pharmacy management system that connects pharmacies with customers for medicine search and inventory management.
https://pharmacy-app-byteme.onrender.com

##Contributors
https://github.com/satvik-phadte.
https://github.com/durgesh3113 
https://github.com/Allen-ctrl-web. 
https://github.com/PankajShahapurkar.
https://github.com/AYUSH22032004

## Features

### For Pharmacies:
- 📍 **Location Management**: Set pharmacy location with coordinates
- 📦 **Inventory Management**: Add, edit, and delete medicine inventory
- 💊 **Medicine Creation**: Create new medicines on the fly
- 📊 **Dashboard**: View inventory statistics and status

### For Customers:
- 📍 **Location Setting**: Set your location to find nearby pharmacies
- 🔍 **Medicine Search**: Search for medicines within a specified distance
- 📱 **Contact Information**: Get pharmacy contact details and directions
- 🗺️ **Distance Calculation**: See how far each pharmacy is from your location

## Technology Stack

- **Backend**: Django 5.2.5
- **Database**: SQLite (default)
- **Frontend**: HTML, CSS, JavaScript
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
```

### Step 4: Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
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

### For Customers:
1. **Register/Login**: Create a regular customer account
2. **Set Location**: Enter your location coordinates
3. **Search Medicines**: Search for specific medicines within your area
4. **Find Pharmacies**: View nearby pharmacies with the medicine you need

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

### CustomerLocation
- Stores customer location for distance calculations
- Fields: user, address, latitude, longitude

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

## Features in Detail

### Distance Calculation
The app uses the Haversine formula to calculate distances between customer and pharmacy locations, providing accurate distance information for medicine searches.

### Inventory Management
- Add new medicines with automatic creation in the database
- Track quantities, prices, and expiry dates
- Set availability status
- View low stock warnings

### Search Functionality
- Search by medicine name
- Filter by maximum distance
- Display pharmacy contact information
- Provide directions via Google Maps

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

3. **Permission Errors**
   - Make sure you're logged in as a pharmacy user for pharmacy features
   - Check user permissions in Django admin

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
