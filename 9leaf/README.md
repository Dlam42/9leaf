# 7_leaf Django Application

A Django web application with user authentication, messaging, and location-based features.

## Project Overview

This project is a Django web application that includes:
- User authentication with Firebase
- Admin and client user roles
- Messaging system between users
- Location-based services using GeoPy
- Request handling system

## Technologies Used

- Django 5.1.5
- Firebase Admin 6.7.0
- GeoPy 2.4.1
- Geographiclib 2.0
- Haversine 2.9.0

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd leaf
```

2. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source myworld/bin/activate
     ```
   - On Windows:
     ```bash
     myworld\Scripts\activate
     ```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python manage.py migrate
```

5. Run the development server:
```bash
python manage.py runserver
```

The application should now be accessible at http://127.0.0.1:8000/

## Project Structure

- `leaf/` - The main Django project configuration
- `members/` - Main application with user management, authentication and messaging
  - `views/` - Contains separated view logic by functionality
  - `templates/` - HTML templates for the application
  - `static/` - Static files (JS, JSON data)
- `jobs/` - Job-related functionality

## Firebase Configuration

The application uses Firebase for authentication. Make sure to configure your Firebase credentials in `leaf/firebase_config.py`.

## Contributing

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)