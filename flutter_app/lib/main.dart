import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'config/theme_config.dart';
import 'config/routes.dart';
import 'providers/auth_provider.dart';
import 'providers/product_provider.dart';
import 'providers/sale_provider.dart';
import 'providers/theme_provider.dart';
import 'providers/active_store_provider.dart';
import 'services/storage_service.dart';
import 'screens/splash_screen.dart';
import 'screens/login_signup_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/quick_sale_screen.dart';
import 'screens/products_screen.dart';
import 'screens/onboarding_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize storage service
  final storageService = StorageService();
  await storageService.init();

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // Theme provider
        ChangeNotifierProvider(
          create: (_) => ThemeProvider(),
        ),
        // Auth provider
        ChangeNotifierProvider(
          create: (_) => AuthProvider(),
        ),
        // Product provider
        ChangeNotifierProvider(
          create: (_) => ProductProvider(),
        ),
        // Sale provider
        ChangeNotifierProvider(
          create: (_) => SaleProvider(),
        ),
        // Active Store globally available
        ChangeNotifierProvider(
          create: (_) => ActiveStoreProvider(),
        ),
      ],
      child: Consumer<ThemeProvider>(
        builder: (context, themeProvider, _) {
          return MaterialApp(
            title: 'Shop Manager',
            theme: ThemeConfig.lightTheme,
            darkTheme: ThemeConfig.darkTheme,
            themeMode:
                themeProvider.isDarkMode ? ThemeMode.dark : ThemeMode.light,
            debugShowCheckedModeBanner: false,
            home: const SplashScreen(),
            routes: _buildRoutes(),
          );
        },
      ),
    );
  }

  Map<String, WidgetBuilder> _buildRoutes() {
    return {
      Routes.login: (context) => const LoginSignupScreen(),
      Routes.dashboard: (context) => const DashboardScreen(),
      Routes.quickSale: (context) => const QuickSaleScreen(),
      Routes.products: (context) => const ProductsScreen(),
      '/onboarding': (context) => const OnboardingScreen(),
    };
  }
}
