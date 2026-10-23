import 'package:flutter/material.dart';

void main() => runApp(const MobilePayApp());

class MobilePayApp extends StatelessWidget {
  const MobilePayApp({super.key});

  @override
  Widget build(BuildContext context) {
    const blue = Color(0xFF2563EB);
    return MaterialApp(
      title: 'MobilePay',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: blue), useMaterial3: true),
      home: Scaffold(
        appBar: AppBar(title: const Text('MobilePay')),
        body: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const SizedBox(height: 20),
            const Text('Welcome to MobilePay', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text('Starter UI only. Connect the API and complete security reviews before real users.'),
            const SizedBox(height: 24),
            Card(child: ListTile(leading: const Icon(Icons.qr_code_2), title: const Text('Scan QR'), subtitle: const Text('Demo placeholder'))),
            Card(child: ListTile(leading: const Icon(Icons.history), title: const Text('Payment history'), subtitle: const Text('Connect /api/payment-history'))),
            Card(child: ListTile(leading: const Icon(Icons.phone_android), title: const Text('Login with mobile OTP'), subtitle: const Text('Connect the OTP endpoints'))),
            const SizedBox(height: 18),
            const Text('No live UPI payments are performed by this starter.', style: TextStyle(color: Colors.deepOrange)),
          ],
        ),
      ),
    );
  }
}
