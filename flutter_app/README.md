# Shop Management SaaS - Flutter App

A modern Flutter mobile application for managing your shop business efficiently. Features include inventory management, quick sales processing, and real-time inventory tracking with a beautiful Dark Mode & Light Mode UI.

## Features

✨ **Authentication**
- User registration and login with JWT tokens
- Secure session management with SharedPreferences
- Mock authentication for development

📊 **Dashboard**
- Real-time inventory statistics
- Quick access to key metrics
- Quick actions for common tasks

🛒 **Quick Sale**
- Fast product selection and checkout
- Discount support
- Multiple payment methods
- Sale notes and tracking

📦 **Inventory Management**
- View all products with profit margins
- Add and edit products
- Track product categories and costs
- Real-time stock management

🎨 **Modern UI/UX**
- Bold & vibrant color scheme (Hot Pink #FF006E, Cyan #00D9FF)
- Dark Mode & Light Mode support
- Smooth animations and transitions
- Responsive mobile design

## Prerequisites

### System Requirements
- Flutter 3.0.0 or higher
- Dart 3.0.0 or higher
- Android Studio or Xcode for emulator/simulator
- Windows, macOS, or Linux development machine

### Backend Requirements
- Flask API running on `http://localhost:5000`
- MySQL database for persistence
- Backend API endpoints for:
  - `/api/v1/auth/login`
  - `/api/v1/auth/signup`
  - `/api/v1/products`
  - `/api/v1/sales`

## Installation

### 1. Clone the Repository

```bash
cd "d:\my first business"
cd flutter_app
```

### 2. Install Dependencies

```bash
flutter pub get
```

### 3. Run the App

#### On Android Emulator
```bash
flutter run -d emulator-5554
```

#### On iOS Simulator (macOS only)
```bash
flutter run -d apple_ios
```

#### On Physical Device
```bash
# Connect your device and run:
flutter run
```

### 4. Build APK/IPA

#### Android APK
```bash
flutter build apk --release
```

#### iOS IPA (macOS only)
```bash
flutter build ipa
```

## Project Structure

```
lib/
├── main.dart                    # App entry point
├── config/
│   ├── app_config.dart         # API URLs and constants
│   ├── theme_config.dart       # Light and dark themes
│   └── routes.dart             # Route definitions
├── models/
│   ├── user_model.dart         # User entity
│   ├── product_model.dart      # Product entity
│   └── sale_model.dart         # Sale and SaleItem entities
├── services/
│   ├── api_service.dart        # HTTP client wrapper
│   ├── auth_service.dart       # Authentication logic
│   ├── product_service.dart    # Product API calls
│   └── storage_service.dart    # SharedPreferences wrapper
├── providers/
│   ├── auth_provider.dart      # Auth state management
│   ├── product_provider.dart   # Products state management
│   ├── sale_provider.dart      # Sale state management
│   └── theme_provider.dart     # Theme toggle state
├── screens/
│   ├── splash_screen.dart      # Loading/splash screen
│   ├── login_signup_screen.dart # Auth screens
│   ├── dashboard_screen.dart   # Home dashboard
│   ├── quick_sale_screen.dart  # Quick checkout
│   └── products_screen.dart    # Inventory management
├── widgets/
│   ├── bottom_nav_bar.dart     # Navigation bar
│   ├── product_card.dart       # Product display card
│   ├── custom_input_field.dart # Reusable input field
│   └── sale_btn.dart           # Reusable button
└── utils/
    ├── constants.dart          # App constants
    └── validators.dart         # Form validators
```

## Configuration

### API Configuration

Edit `lib/config/app_config.dart` to configure the backend API:

```dart
static const String baseUrl = 'http://localhost:5000';
static const bool useMockData = true; // Set to false to use real API
```

**Note:** The app includes mock data support for development without a running backend. Switch `useMockData` to `true` for testing.

### Theme Colors

Colors are defined in `lib/config/theme_config.dart`:
- **Primary:** Hot Pink `#FF006E`
- **Accent:** Cyan `#00D9FF`
- **Secondary:** Electric Purple `#7C3AED`

## Demo Credentials (Mock Mode)

When using mock data:
- **Email:** `user@example.com`
- **Password:** Any password

## Dependencies

- **provider**: State management
- **http**: HTTP client for API calls
- **shared_preferences**: Local storage for JWT tokens
- **google_fonts**: Modern typography
- **flutter_dotenv**: Environment configuration

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/signup` - User registration

### Products
- `GET /api/v1/products` - Fetch all products
- `GET /api/v1/products/{id}` - Fetch single product
- `POST /api/v1/products` - Create product
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product

### Sales
- `POST /api/v1/sales` - Create sale
- `GET /api/v1/sales` - Fetch sales history

## Development

### Hot Reload
During development, use hot reload to see changes instantly:

```bash
# In the running app console, press 'r'
r     - Hot reload
R     - Hot restart
```

### Device Debugging

```bash
# Verbose logging
flutter run -v

# Enable web debugging (Chrome DevTools)
flutter run --web-devtools
```

## Troubleshooting

### Issue: "Flutter not found"
**Solution:** Install Flutter from https://flutter.dev/docs/get-started/install

### Issue: "Doctor issues with Android/iOS"
```bash
flutter doctor --android-licenses
flutter doctor -v
```

### Issue: "MockHttpClient errors with real API"
**Solution:** Ensure backend is running on `localhost:5000` and set `useMockData = false`

### Issue: "Token expiration errors"
**Solution:** Clear app data and database, login again

## Testing

Future release will include:
- Unit tests for models and services
- Widget tests for screens
- Integration tests with backend

## Performance Tips

1. **Image Optimization:** Use cached network images for product images
2. **State Management:** Use ChangeNotifier efficiently
3. **Database:** Consider using Hive for offline caching
4. **API:** Implement request debouncing for search/filter

## Build & Deployment

### Android Play Store
```bash
flutter build appbundle --release
# Upload to Google Play Console
```

### iOS App Store (macOS)
```bash
flutter build ipa --release
# Upload to App Store Connect
```

## Contributing

Guidelines for contributing:
1. Follow Dart style guide
2. Write clean, readable code
3. Test on both Android and iOS
4. Update this README with new features

## License

This project is proprietary software for Shop Management SaaS platform.

## Support

For issues and questions, contact the development team.

## Changelog

### Version 1.0.0 (Initial Release)
- ✅ Splash screen with animations
- ✅ User authentication (login/signup)
- ✅ Dashboard with statistics
- ✅ Product inventory management
- ✅ Quick sale functionality
- ✅ Dark mode and light mode
- ✅ Mock API for development
- ✅ Bottom navigation bar
