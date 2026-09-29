import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/active_store_provider.dart';
import '../services/store_service.dart';
import '../widgets/custom_input_field.dart';
import '../widgets/sale_btn.dart';
import '../config/theme_config.dart';
import '../utils/validators.dart';
import '../config/routes.dart';

class LoginSignupScreen extends StatefulWidget {
  const LoginSignupScreen({Key? key}) : super(key: key);

  @override
  State<LoginSignupScreen> createState() => _LoginSignupScreenState();
}

class _LoginSignupScreenState extends State<LoginSignupScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  // Login form
  final _loginFormKey = GlobalKey<FormState>();
  final _loginEmailController = TextEditingController();
  final _loginPasswordController = TextEditingController();

  // Signup form
  final _signupFormKey = GlobalKey<FormState>();
  final _signupEmailController = TextEditingController();
  final _signupUsernameController = TextEditingController();
  final _signupPasswordController = TextEditingController();
  final _signupShopNameController = TextEditingController();
  final _signupConfirmPasswordController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _loginEmailController.dispose();
    _loginPasswordController.dispose();
    _signupEmailController.dispose();
    _signupUsernameController.dispose();
    _signupPasswordController.dispose();
    _signupShopNameController.dispose();
    _signupConfirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin(BuildContext context) async {
    if (!_loginFormKey.currentState!.validate()) return;

    final authProvider = context.read<AuthProvider>();
    final result = await authProvider.login(
      _loginEmailController.text.trim(),
      _loginPasswordController.text,
    );

    if (result['success'] == true && context.mounted) {
      if (result['is_onboarded'] == true) {
        // Fetch active store
        try {
          final stores = await StoreService().getUserStores(token: result['token']);
          if (stores.isNotEmpty && context.mounted) {
             context.read<ActiveStoreProvider>().setActiveStore(stores[0]['id'], stores[0]['store_name']);
             context.read<ActiveStoreProvider>().setOnboarded(true);
             Navigator.of(context).pushReplacementNamed(Routes.dashboard);
          } else if (context.mounted) {
             Navigator.of(context).pushReplacementNamed('/onboarding');
          }
        } catch (e) {
          if (context.mounted) Navigator.of(context).pushReplacementNamed('/onboarding');
        }
      } else {
        Navigator.of(context).pushReplacementNamed('/onboarding');
      }
    } else if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(authProvider.error ?? 'Login failed')),
      );
    }
  }

  Future<void> _handleSignup(BuildContext context) async {
    if (!_signupFormKey.currentState!.validate()) return;

    if (_signupPasswordController.text !=
        _signupConfirmPasswordController.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Passwords do not match')),
      );
      return;
    }

    final authProvider = context.read<AuthProvider>();
    final result = await authProvider.signup(
      email: _signupEmailController.text.trim(),
      username: _signupUsernameController.text.trim(),
      password: _signupPasswordController.text,
      shopName: _signupShopNameController.text.trim(),
    );

    if (result['success'] == true && context.mounted) {
      // Signup always goes to onboarding
      Navigator.of(context).pushReplacementNamed('/onboarding');
    } else if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(authProvider.error ?? 'Signup failed')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Gradient header
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    ThemeConfig.primaryColor,
                    ThemeConfig.secondaryColor,
                  ],
                ),
              ),
              child: Column(
                children: [
                  Icon(
                    Icons.store,
                    size: 48,
                    color: Colors.white,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Shop Manager',
                    style: GoogleFonts.poppins(
                      fontSize: 24,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
            ),

            // Tab bar
            TabBar(
              controller: _tabController,
              indicatorColor: ThemeConfig.primaryColor,
              labelStyle: GoogleFonts.poppins(
                fontWeight: FontWeight.w600,
                fontSize: 16,
              ),
              unselectedLabelStyle: GoogleFonts.poppins(
                fontWeight: FontWeight.w400,
                fontSize: 16,
              ),
              tabs: const [
                Tab(text: 'Login'),
                Tab(text: 'Sign Up'),
              ],
            ),

            // Tab content
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  // Login Tab
                  _buildLoginTab(context),

                  // Signup Tab
                  _buildSignupTab(context),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLoginTab(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, _) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _loginFormKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 24),
                Text(
                  'Welcome Back!',
                  style: GoogleFonts.poppins(
                    fontSize: 28,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Log in to your shop account',
                  style: GoogleFonts.inter(
                    fontSize: 14,
                    color: Colors.grey,
                  ),
                ),
                const SizedBox(height: 32),
                CustomInputField(
                  label: 'Email',
                  hint: 'Enter your email',
                  controller: _loginEmailController,
                  keyboardType: TextInputType.emailAddress,
                  prefixIcon: Icons.email,
                  validator: Validators.validateEmail,
                ),
                CustomInputField(
                  label: 'Password',
                  hint: 'Enter your password',
                  controller: _loginPasswordController,
                  obscureText: true,
                  prefixIcon: Icons.lock,
                  validator: Validators.validatePassword,
                ),
                const SizedBox(height: 24),
                SaleButton(
                  label: 'Login',
                  isLoading: authProvider.isLoading,
                  onPressed: () => _handleLogin(context),
                ),
                const SizedBox(height: 16),
                Center(
                  child: Text(
                    'Demo: user@example.com / password any',
                    style: GoogleFonts.inter(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildSignupTab(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, _) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _signupFormKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 24),
                Text(
                  'Create Account',
                  style: GoogleFonts.poppins(
                    fontSize: 28,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Start managing your shop today',
                  style: GoogleFonts.inter(
                    fontSize: 14,
                    color: Colors.grey,
                  ),
                ),
                const SizedBox(height: 32),
                CustomInputField(
                  label: 'Email',
                  hint: 'Enter your email',
                  controller: _signupEmailController,
                  keyboardType: TextInputType.emailAddress,
                  prefixIcon: Icons.email,
                  validator: Validators.validateEmail,
                ),
                CustomInputField(
                  label: 'Username',
                  hint: 'Choose a username',
                  controller: _signupUsernameController,
                  prefixIcon: Icons.person,
                  validator: Validators.validateUsername,
                ),
                CustomInputField(
                  label: 'Shop Name',
                  hint: 'Enter your shop name',
                  controller: _signupShopNameController,
                  prefixIcon: Icons.store,
                  validator: Validators.validateShopName,
                ),
                CustomInputField(
                  label: 'Password',
                  hint: 'Create a password',
                  controller: _signupPasswordController,
                  obscureText: true,
                  prefixIcon: Icons.lock,
                  validator: Validators.validatePassword,
                ),
                CustomInputField(
                  label: 'Confirm Password',
                  hint: 'Confirm your password',
                  controller: _signupConfirmPasswordController,
                  obscureText: true,
                  prefixIcon: Icons.lock,
                  validator: Validators.validatePassword,
                ),
                const SizedBox(height: 24),
                SaleButton(
                  label: 'Sign Up',
                  isLoading: authProvider.isLoading,
                  onPressed: () => _handleSignup(context),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
