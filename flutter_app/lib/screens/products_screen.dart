import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/product_provider.dart';
import '../providers/auth_provider.dart';
import '../providers/active_store_provider.dart';
import '../widgets/product_card.dart';
import '../widgets/custom_input_field.dart';
import '../widgets/sale_btn.dart';
import '../config/theme_config.dart';
import '../utils/validators.dart';
import '../utils/constants.dart';

class ProductsScreen extends StatefulWidget {
  const ProductsScreen({Key? key}) : super(key: key);

  @override
  State<ProductsScreen> createState() => _ProductsScreenState();
}

class _ProductsScreenState extends State<ProductsScreen> {
  bool _showAddForm = false;
  final _nameController = TextEditingController();
  final _priceController = TextEditingController();
  final _costController = TextEditingController();
  final _quantityController = TextEditingController();
  final _descriptionController = TextEditingController();
  String _selectedCategory = 'Electronics';
  final _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _loadProducts();
  }

  Future<void> _loadProducts() async {
    final authProvider = context.read<AuthProvider>();
    final productProvider = context.read<ProductProvider>();
    final activeStoreProvider = context.read<ActiveStoreProvider>();

    if (productProvider.products.isEmpty) {
      await productProvider.fetchProducts(
        activeStoreProvider.activeStoreId!,
        token: authProvider.token,
      );
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _priceController.dispose();
    _costController.dispose();
    _quantityController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _addProduct(ProductProvider productProvider, String token, int storeId) async {
    if (!_formKey.currentState!.validate()) return;

    final success = await productProvider.addProduct(
      storeId,
      _nameController.text.trim(),
      double.parse(_priceController.text),
      description: _descriptionController.text.trim(),
      quantity: int.parse(_quantityController.text),
      category: _selectedCategory,
      cost: _costController.text.isNotEmpty
          ? double.parse(_costController.text)
          : null,
      token: token,
    );

    if (success && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Product added successfully')),
      );

      _nameController.clear();
      _priceController.clear();
      _costController.clear();
      _quantityController.clear();
      _descriptionController.clear();

      setState(() {
        _showAddForm = false;
      });
    } else if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(productProvider.error ?? 'Failed to add product'),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Products'),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () {
              setState(() {
                _showAddForm = !_showAddForm;
              });
            },
          ),
        ],
      ),
      body: Consumer<ProductProvider>(
        builder: (context, productProvider, _) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Add product form
                if (_showAddForm) ...[
                  _buildAddProductForm(productProvider),
                  const SizedBox(height: 24),
                ],

                // Products list
                if (productProvider.isLoading)
                  const Center(
                    child: CircularProgressIndicator(),
                  )
                else if (productProvider.products.isEmpty)
                  Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 48),
                      child: Column(
                        children: [
                          Icon(
                            Icons.inbox,
                            size: 64,
                            color: Colors.grey.withOpacity(0.3),
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'No products yet',
                            style: GoogleFonts.poppins(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Add your first product to get started',
                            style: GoogleFonts.inter(
                              fontSize: 14,
                              color: Colors.grey,
                            ),
                          ),
                        ],
                      ),
                    ),
                  )
                else
                  Column(
                    children: [
                      Text(
                        '${productProvider.products.length} Products',
                        style: GoogleFonts.poppins(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 12),
                      GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        gridDelegate:
                            const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 2,
                          mainAxisSpacing: 12,
                          crossAxisSpacing: 12,
                          childAspectRatio: 0.85,
                        ),
                        itemCount: productProvider.products.length,
                        itemBuilder: (context, index) {
                          final product = productProvider.products[index];

                          return ProductCard(
                            product: product,
                            onDelete: () {
                              _confirmDelete(context, productProvider, product.id);
                            },
                          );
                        },
                      ),
                    ],
                  ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildAddProductForm(ProductProvider productProvider) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, _) {
        return Card(
          elevation: 4,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Add New Product',
                    style: GoogleFonts.poppins(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 16),
                  CustomInputField(
                    label: 'Product Name',
                    hint: 'Enter product name',
                    controller: _nameController,
                    prefixIcon: Icons.inventory,
                    validator: Validators.validateProductName,
                  ),
                  Row(
                    children: [
                      Expanded(
                        child: CustomInputField(
                          label: 'Price',
                          hint: '0.00',
                          controller: _priceController,
                          keyboardType: TextInputType.number,
                          prefixIcon: Icons.attach_money,
                          validator: Validators.validatePrice,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: CustomInputField(
                          label: 'Cost',
                          hint: '0.00',
                          controller: _costController,
                          keyboardType: TextInputType.number,
                          prefixIcon: Icons.money,
                        ),
                      ),
                    ],
                  ),
                  CustomInputField(
                    label: 'Quantity',
                    hint: '0',
                    controller: _quantityController,
                    keyboardType: TextInputType.number,
                    prefixIcon: Icons.add_box,
                    validator: Validators.validateQuantity,
                  ),
                  Text(
                    'Category',
                    style: GoogleFonts.poppins(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  DropdownButton<String>(
                    isExpanded: true,
                    value: _selectedCategory,
                    items: productCategories.map((category) {
                      return DropdownMenuItem(
                        value: category,
                        child: Text(category),
                      );
                    }).toList(),
                    onChanged: (value) {
                      if (value != null) {
                        setState(() {
                          _selectedCategory = value;
                        });
                      }
                    },
                  ),
                  const SizedBox(height: 16),
                  CustomInputField(
                    label: 'Description',
                    hint: 'Enter product description',
                    controller: _descriptionController,
                    maxLines: 3,
                    minLines: 2,
                  ),
                  const SizedBox(height: 16),
                  SaleButton(
                    label: 'Add Product',
                    isLoading: productProvider.isLoading,
                    onPressed: () =>
                        _addProduct(productProvider, authProvider.token ?? '', context.read<ActiveStoreProvider>().activeStoreId ?? 0),
                    icon: Icons.add,
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: OutlinedButton(
                      onPressed: () {
                        setState(() {
                          _showAddForm = false;
                        });
                        _nameController.clear();
                        _priceController.clear();
                        _costController.clear();
                        _quantityController.clear();
                        _descriptionController.clear();
                      },
                      child: const Text('Cancel'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  void _confirmDelete(
    BuildContext context,
    ProductProvider productProvider,
    int productId,
  ) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Product?'),
        content:
            const Text('Are you sure you want to delete this product?'),
        actions: [
          TextButton(
            child: const Text('Cancel'),
            onPressed: () => Navigator.pop(context),
          ),
          TextButton(
            child: const Text('Delete',
                style: TextStyle(color: ThemeConfig.errorColor)),
            onPressed: () {
              Navigator.pop(context);
              final authProvider = context.read<AuthProvider>();
              final activeStoreProvider = context.read<ActiveStoreProvider>();
              productProvider.deleteProduct(
                activeStoreProvider.activeStoreId ?? 0,
                productId,
                token: authProvider.token,
              );
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Product deleted')),
              );
            },
          ),
        ],
      ),
    );
  }
}
