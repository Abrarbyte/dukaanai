import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/sale_provider.dart';
import '../providers/product_provider.dart';
import '../providers/auth_provider.dart';
import '../models/sale_model.dart';
import '../widgets/sale_btn.dart';
import '../widgets/custom_input_field.dart';
import '../config/theme_config.dart';
import '../utils/constants.dart';

class QuickSaleScreen extends StatefulWidget {
  const QuickSaleScreen({Key? key}) : super(key: key);

  @override
  State<QuickSaleScreen> createState() => _QuickSaleScreenState();
}

class _QuickSaleScreenState extends State<QuickSaleScreen> {
  final _discountController = TextEditingController();
  final _notesController = TextEditingController();
  String _selectedPaymentMethod = 'Cash';
  int? _selectedProductId;
  int _selectedQuantity = 1;

  @override
  void dispose() {
    _discountController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Quick Sale'),
        elevation: 0,
      ),
      body: Consumer<SaleProvider>(
        builder: (context, saleProvider, _) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Product selection
                _buildProductSelection(saleProvider),
                const SizedBox(height: 24),

                // Cart items
                if (saleProvider.cartItems.isNotEmpty) ...[
                  Text(
                    'Cart Items',
                    style: GoogleFonts.poppins(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildCartItems(saleProvider),
                  const SizedBox(height: 24),
                ] else
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 32),
                    child: Center(
                      child: Text(
                        'No items in cart',
                        style: GoogleFonts.inter(
                          color: Colors.grey,
                          fontSize: 14,
                        ),
                      ),
                    ),
                  ),

                // Payment details
                if (saleProvider.cartItems.isNotEmpty) ...[
                  Text(
                    'Payment Details',
                    style: GoogleFonts.poppins(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildPaymentSection(saleProvider),
                  const SizedBox(height: 24),

                  // Total summary
                  _buildTotalSummary(saleProvider),
                  const SizedBox(height: 24),

                  // Complete sale button
                  SaleButton(
                    label: 'Complete Sale',
                    onPressed: () => _completeSale(saleProvider),
                    icon: Icons.check_circle,
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: OutlinedButton(
                      onPressed: () {
                        saleProvider.clearCart();
                        _discountController.clear();
                        _notesController.clear();
                      },
                      child: const Text('Clear Cart'),
                    ),
                  ),
                ],
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildProductSelection(SaleProvider saleProvider) {
    return Consumer<ProductProvider>(
      builder: (context, productProvider, _) {
        final availableProducts = productProvider.products
            .where((p) => p.quantity > 0)
            .toList();

        return Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Select Product',
                  style: GoogleFonts.poppins(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButton<int>(
                  isExpanded: true,
                  value: _selectedProductId,
                  hint: const Text('Choose a product'),
                  items: availableProducts.map((product) {
                    return DropdownMenuItem(
                      value: product.id,
                      child: Text(
                          '${product.name} (\$${product.price.toStringAsFixed(2)})'),
                    );
                  }).toList(),
                  onChanged: (value) {
                    setState(() {
                      _selectedProductId = value;
                      _selectedQuantity = 1;
                    });
                  },
                ),
                if (_selectedProductId != null) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Quantity',
                              style: GoogleFonts.inter(fontSize: 12),
                            ),
                            Row(
                              children: [
                                IconButton(
                                  icon: const Icon(Icons.remove),
                                  onPressed: _selectedQuantity > 1
                                      ? () {
                                          setState(() {
                                            _selectedQuantity--;
                                          });
                                        }
                                      : null,
                                ),
                                Text(
                                  '$_selectedQuantity',
                                  style: GoogleFonts.poppins(
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                IconButton(
                                  icon: const Icon(Icons.add),
                                  onPressed: () {
                                    setState(() {
                                      _selectedQuantity++;
                                    });
                                  },
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      SizedBox(
                        height: 48,
                        child: ElevatedButton.icon(
                          onPressed: _addItemToCart(
                            saleProvider,
                            productProvider,
                          ),
                          icon: const Icon(Icons.add_shopping_cart),
                          label: const Text('Add'),
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }

  VoidCallback? _addItemToCart(
    SaleProvider saleProvider,
    ProductProvider productProvider,
  ) {
    if (_selectedProductId == null) return null;

    return () {
      final product = productProvider.products
          .firstWhere((p) => p.id == _selectedProductId);

      final saleItem = SaleItem(
        productId: product.id,
        productName: product.name,
        quantity: _selectedQuantity,
        unitPrice: product.price,
        totalPrice: _selectedQuantity * product.price,
      );

      saleProvider.addItem(saleItem);
      _selectedProductId = null;
      _selectedQuantity = 1;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Item added to cart')),
      );
    };
  }

  Widget _buildCartItems(SaleProvider saleProvider) {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: saleProvider.cartItems.length,
      itemBuilder: (context, index) {
        final item = saleProvider.cartItems[index];

        return Card(
          child: ListTile(
            title: Text(item.productName),
            subtitle: Text(
              'Qty: ${item.quantity} x \$${item.unitPrice.toStringAsFixed(2)}',
            ),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '\$${item.totalPrice.toStringAsFixed(2)}',
                  style: GoogleFonts.poppins(
                    fontWeight: FontWeight.w600,
                    color: ThemeConfig.primaryColor,
                  ),
                ),
                SizedBox(
                  width: 80,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.close),
                        iconSize: 18,
                        onPressed: () {
                          saleProvider.removeItem(item.productId);
                        },
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildPaymentSection(SaleProvider saleProvider) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Payment Method',
              style: GoogleFonts.inter(
                fontSize: 12,
                color: Colors.grey,
              ),
            ),
            const SizedBox(height: 8),
            DropdownButton<String>(
              isExpanded: true,
              value: _selectedPaymentMethod,
              items: paymentMethods.map((method) {
                return DropdownMenuItem(
                  value: method,
                  child: Text(method),
                );
              }).toList(),
              onChanged: (value) {
                if (value != null) {
                  setState(() {
                    _selectedPaymentMethod = value;
                  });
                  saleProvider.setPaymentMethod(value);
                }
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _discountController,
              decoration: const InputDecoration(
                labelText: 'Discount (\$)',
                hintText: '0.00',
              ),
              keyboardType: TextInputType.number,
              onChanged: (value) {
                final discount = double.tryParse(value) ?? 0;
                saleProvider.setDiscount(discount);
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _notesController,
              decoration: const InputDecoration(
                labelText: 'Notes',
                hintText: 'Add any notes here...',
              ),
              maxLines: 3,
              onChanged: (value) {
                saleProvider.setNotes(value.isEmpty ? null : value);
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTotalSummary(SaleProvider saleProvider) {
    return Card(
      color: ThemeConfig.primaryColor.withOpacity(0.05),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Subtotal:',
                  style: GoogleFonts.inter(fontSize: 14),
                ),
                Text(
                  '\$${saleProvider.totalAmount.toStringAsFixed(2)}',
                  style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
                ),
              ],
            ),
            if (saleProvider.discount > 0) ...[
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Discount:',
                    style: GoogleFonts.inter(fontSize: 14),
                  ),
                  Text(
                    '-\$${saleProvider.discount.toStringAsFixed(2)}',
                    style: GoogleFonts.poppins(
                      fontWeight: FontWeight.w600,
                      color: ThemeConfig.accentColor,
                    ),
                  ),
                ],
              ),
            ],
            const Divider(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Total:',
                  style: GoogleFonts.poppins(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Text(
                  '\$${saleProvider.finalAmount.toStringAsFixed(2)}',
                  style: GoogleFonts.poppins(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    color: ThemeConfig.primaryColor,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _completeSale(SaleProvider saleProvider) {
    final sale = saleProvider.getSale();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Sale completed! Total: \$${sale.finalAmount.toStringAsFixed(2)}',
        ),
        duration: const Duration(seconds: 2),
      ),
    );

    saleProvider.clearCart();
    _discountController.clear();
    _notesController.clear();
  }
}
