# Getting Started - Setup Checklist

## Prerequisites Setup

### Step 1: Install Flutter SDK
- [ ] Download Flutter SDK from https://flutter.dev/docs/get-started/install
- [ ] Extract to a location (e.g., `C:\flutter` on Windows)
- [ ] Add Flutter to PATH:
  - Windows: Add `C:\flutter\bin` to system PATH
  - macOS/Linux: Add to `.bashrc` or `.zshrc`
- [ ] Run `flutter doctor` to verify installation
- [ ] Resolve any issues shown by `flutter doctor`

### Step 2: Install Android/iOS Development Tools

#### For Android:
- [ ] Install Android Studio from https://developer.android.com/studio
- [ ] Accept Android licenses: `flutter doctor --android-licenses`
- [ ] Create virtual device in Android Studio
- [ ] Or use USB debugging on physical device

#### For iOS (macOS only):
- [ ] Install Xcode from App Store
- [ ] Run `sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer`
- [ ] Accept Xcode licenses: `sudo xcodebuild -license accept`
- [ ] Install iOS pods: `cd ios && pod install`

### Step 3: Verify Installation
- [ ] Run `flutter doctor -v`
- [ ] All items should have checkmarks ✓

## Project Setup

### Step 1: Navigate to Project
```bash
cd "d:\my first business\flutter_app"
```

### Step 2: Get Dependencies
```bash
flutter pub get
```

### Step 3: Generate Code (if needed)
```bash
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

## Running the App

### Option 1: Run on Emulator/Simulator
```bash
# Android
flutter emulators
flutter emulators launch <emulator_name>
flutter run

# iOS (macOS only)
flutter run -d "iPhone 15 Pro"
```

### Option 2: Run on Physical Device
```bash
# Connect device with USB debugging enabled
flutter devices
flutter run -d <device_id>
```

### Option 3: Run on Web (Preview)
```bash
flutter run -d web-server
# Open browser to http://localhost:port
```

## Backend Setup

### Option 1: Use Mock Data (Development)
- App is configured to use mock data by default
- Mock credentials: `user@example.com` / any password
- No backend required for initial testing

### Option 2: Switch to Real API
1. Edit `lib/config/app_config.dart`
2. Set `useMockData = false`
3. Ensure Flask backend is running on `http://localhost:5000`

### Backend API Checklist:
- [ ] Python 3.8+ installed
- [ ] Virtual environment activated: `python -m venv venv`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Database configured and migrated
- [ ] Flask server running: `python run.py`
- [ ] API responding at `http://localhost:5000/api/v1/health`

## App Features to Test

### Authentication
- [ ] Splash screen loads and animates
- [ ] Login screen displays properly
- [ ] Can input email and password
- [ ] Submit login/signup form
- [ ] Error messages display on failure
- [ ] Successful login redirects to dashboard

### Dashboard
- [ ] Dashboard loads after login
- [ ] Statistics cards display correctly
- [ ] Quick action buttons work
- [ ] Logout functionality works

### Products
- [ ] Products list loads
- [ ] Can see product details (price, stock, profit)
- [ ] Can add new product
- [ ] Form validation works
- [ ] Products grid displays 2 columns
- [ ] Can delete products

### Quick Sale
- [ ] Can select products
- [ ] Quantity increment/decrement works
- [ ] Add to cart functionality works
- [ ] Cart displays items and totals
- [ ] Discount input works
- [ ] Payment method selection works
- [ ] Complete sale button works

### Dark Mode
- [ ] Toggle dark/light mode from settings
- [ ] Theme persists after app restart
- [ ] Colors are correct for light mode
- [ ] Colors are correct for dark mode

## Troubleshooting

### Common Issues

**Issue: "flutter: command not found"**
- Solution: Add Flutter to PATH and restart terminal

**Issue: "Android emulator not found"**
- Solution: Create emulator in Android Studio: AVD Manager → Create Virtual Device

**Issue: "cocoapods error" (iOS)**
- Solution: Run `cd ios && pod repo update && pod install`

**Issue: "Package not found" errors**
- Solution: Run `flutter pub get` and `flutter pub upgrade`

**Issue: "Gradle build failed"**
- Solution: Run `flutter clean` then `flutter pub get`

**Issue: "API 404 errors" with backend**
- Solution: Check backend is running, verify URL in app_config.dart

## Performance Tips

1. Use hot reload during development: Press `r` in terminal
2. Use hot restart if hot reload fails: Press `R`
3. Check performance using DevTools:
   ```bash
   flutter pub global activate devtools
   devtools
   ```

## Next Steps

- [ ] Customize app colors in `lib/config/theme_config.dart`
- [ ] Update app name and icons
- [ ] Connect to production backend
- [ ] Set up CI/CD pipeline
- [ ] Add push notifications
- [ ] Implement offline caching with Hive
- [ ] Add analytics tracking

## Resources

- [Flutter Documentation](https://flutter.dev/docs)
- [Provider Package](https://pub.dev/packages/provider)
- [Dart Language Tour](https://dart.dev/guides/language/language-tour)
- [Material Design](https://material.io/design)

## Support

For issues:
1. Check the README.md for detailed documentation
2. Run `flutter doctor` to diagnose environment issues
3. Check logcat for Android errors: `flutter logs`
4. Check console output for errors
5. Search Flutter issues: https://github.com/flutter/flutter/issues

---

**Last Updated:** 2026-04-19
**Flutter App Version:** 1.0.0
