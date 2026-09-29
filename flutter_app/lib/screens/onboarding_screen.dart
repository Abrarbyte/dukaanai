import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../config/app_config.dart';
import '../config/theme_config.dart';
import '../config/routes.dart';
import '../services/api_service.dart';
import '../widgets/custom_input_field.dart';
import '../widgets/sale_btn.dart';
import '../providers/active_store_provider.dart';
import '../providers/auth_provider.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({Key? key}) : super(key: key);

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  int _currentStep = 0;
  bool _isLoading = false;

  final _storeFormKey = GlobalKey<FormState>();
  final _storeNameController = TextEditingController();
  final _addressController = TextEditingController();

  final ApiService _apiService = ApiService();

  @override
  void dispose() {
    _storeNameController.dispose();
    _addressController.dispose();
    super.dispose();
  }

  Future<void> _createStore() async {
    if (!_storeFormKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    try {
      final authProvider = context.read<AuthProvider>();
      print('🔍 Onboarding: Creating store with token: ${authProvider.token}');

      final response = await _apiService.post(
        '/api/stores',
        body: {
          'store_name': _storeNameController.text.trim(),
          'address': _addressController.text.trim(),
          'store_type': 'General',
        },
        token: authProvider.token,
      );

      // Save to ActiveStoreProvider
      if (mounted && response != null) {
         context.read<ActiveStoreProvider>().setActiveStore(response['id'], response['store_name']);
      }

      setState(() {
        _currentStep++;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to create store: $e')),
        );
      }
    }
  }

  Future<void> _completeOnboarding() async {
    setState(() => _isLoading = true);
    try {
      final authProvider = context.read<AuthProvider>();
      print('🔍 Onboarding: Completing onboarding with token: ${authProvider.token}');

      await _apiService.post('/api/onboarding/complete', body: {}, token: authProvider.token);

      if (mounted) {
        context.read<ActiveStoreProvider>().setOnboarded(true);
        Navigator.of(context).pushReplacementNamed(Routes.dashboard);
      }
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to complete onboarding: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Setup Your Shop', style: GoogleFonts.poppins()),
        automaticallyImplyLeading: false,
      ),
      body: Stepper(
        currentStep: _currentStep,
        onStepContinue: () {
          if (_currentStep == 0) {
            _createStore();
          } else if (_currentStep == 1) {
            _completeOnboarding();
          }
        },
        controlsBuilder: (context, details) {
          return Padding(
            padding: const EdgeInsets.only(top: 16.0),
            child: SaleButton(
              label: _currentStep == 0 ? 'Create Store' : 'Go to Dashboard',
              onPressed: details.onStepContinue ?? () {},
              isLoading: _isLoading,
            ),
          );
        },
        steps: [
          Step(
            title: Text('Store Details', style: GoogleFonts.poppins()),
            content: Form(
              key: _storeFormKey,
              child: Column(
                children: [
                  CustomInputField(
                    label: 'Store Name',
                    hint: 'Enter your business name',
                    controller: _storeNameController,
                    prefixIcon: Icons.store,
                    validator: (val) => val == null || val.isEmpty ? 'Required' : null,
                  ),
                  CustomInputField(
                    label: 'Store Address',
                    hint: 'Enter physical address',
                    controller: _addressController,
                    prefixIcon: Icons.location_on,
                    validator: (val) => val == null || val.isEmpty ? 'Required' : null,
                  ),
                ],
              ),
            ),
            isActive: _currentStep >= 0,
            state: _currentStep > 0 ? StepState.complete : StepState.editing,
          ),
          Step(
            title: Text('Ready to Go!', style: GoogleFonts.poppins()),
            content: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Your store has been created! You can add products and manage your inventory from the dashboard.',
                  style: GoogleFonts.inter(fontSize: 16),
                )
              ],
            ),
            isActive: _currentStep >= 1,
            state: _currentStep > 1 ? StepState.complete : StepState.indexed,
          ),
        ],
      ),
    );
  }
}
