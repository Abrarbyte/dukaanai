import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/active_store_provider.dart';
import '../providers/theme_provider.dart';
import '../services/store_service.dart';
import '../widgets/bottom_nav_bar.dart';
import '../config/theme_config.dart';
import '../config/routes.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentNavIndex = 0;
  bool _isLoading = true;
  Map<String, dynamic>? _dashboardData;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadDashboardData();
    });
  }

  Future<void> _loadDashboardData() async {
    final activeStore = context.read<ActiveStoreProvider>();
    final authProvider = context.read<AuthProvider>();

    if (activeStore.activeStoreId != null) {
      final data = await StoreService().getDashboard(
        activeStore.activeStoreId!,
        token: authProvider.token,
      );
      if (mounted) {
        setState(() {
          _dashboardData = data;
          _isLoading = false;
        });
      }
    } else {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Consumer<ActiveStoreProvider>(
          builder: (context, store, _) => Text(store.activeStoreName ?? 'Dashboard'),
        ),
        elevation: 0,
        actions: [
          Consumer<ThemeProvider>(
            builder: (context, themeProvider, _) {
              return IconButton(
                icon: Icon(
                  themeProvider.isDarkMode
                      ? Icons.light_mode
                      : Icons.dark_mode,
                ),
                onPressed: () => themeProvider.toggleTheme(),
              );
            },
          ),
          Consumer<AuthProvider>(
            builder: (context, authProvider, _) {
              return IconButton(
                icon: const Icon(Icons.logout),
                onPressed: () async {
                  await authProvider.logout();
                  if (context.mounted) {
                    Navigator.of(context)
                        .pushReplacementNamed(Routes.login);
                  }
                },
              );
            },
          ),
        ],
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator()) 
          : RefreshIndicator(
              onRefresh: _loadDashboardData,
              child: _buildContent(),
            ),
      bottomNavigationBar: BottomNavBar(
        currentIndex: _currentNavIndex,
        onTap: _onNavTap,
      ),
    );
  }

  void _onNavTap(int index) {
    setState(() {
      _currentNavIndex = index;
    });

    switch (index) {
      case 0:
        // Dashboard (stay)
        break;
      case 1:
        Navigator.of(context).pushNamed(Routes.quickSale);
        break;
      case 2:
        Navigator.of(context).pushNamed(Routes.products);
        break;
      case 3:
        // Settings (placeholder)
        _showSettingsBottomSheet();
        break;
    }
  }

  Widget _buildContent() {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, _) {
        return SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Welcome section
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Welcome back, ${authProvider.user?.name ?? 'User'}!',
                        style: GoogleFonts.poppins(
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        authProvider.user?.shopName ?? 'Your Shop',
                        style: GoogleFonts.inter(
                          fontSize: 14,
                          color: Colors.grey,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Stats section
              Text(
                'Today\'s Stats',
                style: GoogleFonts.poppins(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 12),
              Builder(
                builder: (context) {
                  final floatRev = _dashboardData?['today']?['revenue'] ?? 0.0;
                  final salesCt = _dashboardData?['today']?['sales_count'] ?? 0;
                  final floatProf = _dashboardData?['today']?['profit'] ?? 0.0;
                  final lowStockAlerts = _dashboardData?['stats']?['low_stock_count'] ?? 0;


                  return GridView.count(
                    crossAxisCount: 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                    children: [
                      _buildStatCard(
                        icon: Icons.attach_money,
                        label: 'Today\'s Sales',
                        value: '\$${floatRev.toStringAsFixed(2)}',
                        color: ThemeConfig.primaryColor,
                      ),
                      _buildStatCard(
                        icon: Icons.trending_up,
                        label: 'Today\'s Profit',
                        value: '\$${floatProf.toStringAsFixed(2)}',
                        color: ThemeConfig.accentColor,
                      ),
                      _buildStatCard(
                        icon: Icons.warning_amber_rounded,
                        label: 'Low Stock',
                        value: '$lowStockAlerts Items',
                        color: ThemeConfig.warningColor,
                      ),
                      _buildStatCard(
                        icon: Icons.shopping_cart,
                        label: 'Orders Count',
                        value: '$salesCt',
                        color: ThemeConfig.secondaryColor,
                      ),
                    ],
                  );
                },
              ),
              const SizedBox(height: 24),

              // Recent actions section
              Text(
                'Quick Actions',
                style: GoogleFonts.poppins(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () {
                    Navigator.of(context).pushNamed(Routes.addProduct);
                  },
                  icon: const Icon(Icons.add),
                  label: const Text('Add Product'),
                ),
              ),
              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () {
                    Navigator.of(context).pushNamed(Routes.products);
                  },
                  icon: const Icon(Icons.list),
                  label: const Text('View Products'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: ThemeConfig.accentColor,
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Recent Sales Section
              Text(
                'Recent Sales',
                style: GoogleFonts.poppins(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 12),
              Builder(
                builder: (context) {
                  final sales = _dashboardData?['recent_sales'] as List<dynamic>? ?? [];
                  if (sales.isEmpty) {
                    return Center(
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Text(
                          'No recent sales yet.',
                          style: GoogleFonts.inter(color: Colors.grey),
                        ),
                      ),
                    );
                  }
                  
                  return ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: sales.length,
                    itemBuilder: (context, index) {
                      final sale = sales[index];
                      // Flask payload example: {'id': 1, 'total_amount': 25.5, ...}
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: ThemeConfig.accentColor.withOpacity(0.1),
                            child: Icon(Icons.receipt_long, color: ThemeConfig.accentColor),
                          ),
                          title: Text(
                            'Order #${sale['id']}',
                            style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
                          ),
                          subtitle: Text(
                            'Paid via ${sale['payment_mode']}',
                            style: GoogleFonts.inter(fontSize: 12),
                          ),
                          trailing: Text(
                             '\$${(sale['total_amount'] ?? 0.0).toStringAsFixed(2)}',
                             style: GoogleFonts.poppins(
                                fontWeight: FontWeight.w600,
                                color: ThemeConfig.primaryColor,
                             ),
                          ),
                        ),
                      );
                    },
                  );
                },
              ),
              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
    VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: color, size: 24),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: GoogleFonts.inter(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    value,
                    style: GoogleFonts.poppins(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: color,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showSettingsBottomSheet() {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Settings',
              style: GoogleFonts.poppins(
                fontSize: 20,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 20),
            Consumer<ThemeProvider>(
              builder: (context, themeProvider, _) {
                return ListTile(
                  leading: Icon(
                    themeProvider.isDarkMode
                        ? Icons.dark_mode
                        : Icons.light_mode,
                  ),
                  title: const Text('Dark Mode'),
                  trailing: Switch(
                    value: themeProvider.isDarkMode,
                    onChanged: (_) => themeProvider.toggleTheme(),
                  ),
                );
              },
            ),
            const SizedBox(height: 12),
            ListTile(
              leading: const Icon(Icons.logout),
              title: const Text('Logout'),
              onTap: () {
                Navigator.pop(context);
                context.read<AuthProvider>().logout();
                Navigator.of(context)
                    .pushReplacementNamed(Routes.login);
              },
            ),
          ],
        ),
      ),
    );
  }
}
