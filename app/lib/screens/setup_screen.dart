import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/debate_provider.dart';
import 'debate_screen.dart';
import 'paste_exchange_screen.dart';

class SetupScreen extends StatefulWidget {
  const SetupScreen({super.key});
  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  final _titleController = TextEditingController(text: 'West Bank settlements legality');
  final _partyAController = TextEditingController(text: 'Position A');
  final _partyBController = TextEditingController(text: 'Position B');
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _titleController.dispose();
    _partyAController.dispose();
    _partyBController.dispose();
    super.dispose();
  }

  Future<void> _startDebate() async {
    if (!_formKey.currentState!.validate()) return;
    final provider = context.read<DebateProvider>();
    await provider.createSession(_titleController.text.trim(), _partyAController.text.trim(), _partyBController.text.trim());
    if (provider.session != null && mounted) {
      Navigator.of(context).push(MaterialPageRoute(builder: (_) => const DebateScreen()));
    }
  }

  Future<void> _importExchange() async {
    final provider = context.read<DebateProvider>();
    await provider.createSession(
      _titleController.text.trim().isEmpty ? 'Imported Exchange' : _titleController.text.trim(),
      _partyAController.text.trim().isEmpty ? 'Party A' : _partyAController.text.trim(),
      _partyBController.text.trim().isEmpty ? 'Party B' : _partyBController.text.trim(),
    );
    if (provider.session != null && mounted) {
      Navigator.of(context).push(MaterialPageRoute(builder: (_) => const PasteExchangeScreen()));
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<DebateProvider>();
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        elevation: 0,
        actions: [
          TextButton.icon(
            onPressed: provider.isCreatingSession ? null : _importExchange,
            icon: const Icon(Icons.upload_file, color: Colors.amber, size: 18),
            label: const Text('Import Exchange', style: TextStyle(color: Colors.amber, fontSize: 13)),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 20),
                Center(
                  child: RichText(
                    text: const TextSpan(
                      style: TextStyle(fontSize: 48, fontWeight: FontWeight.w900, letterSpacing: -2),
                      children: [
                        TextSpan(text: 'lio', style: TextStyle(color: Colors.amber)),
                        TextSpan(text: 'Malau', style: TextStyle(color: Colors.white)),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Center(child: Text('Arguments adjudicated by international law', style: TextStyle(color: Colors.grey[500], fontSize: 14))),
                const SizedBox(height: 48),
                const Text('Debate Topic', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
                const SizedBox(height: 8),
                _buildInput(_titleController, 'e.g. West Bank settlements legality'),
                const SizedBox(height: 24),
                const Text('Party A Label', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
                const SizedBox(height: 8),
                _buildInput(_partyAController, 'e.g. Position A'),
                const SizedBox(height: 16),
                const Text('Party B Label', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
                const SizedBox(height: 8),
                _buildInput(_partyBController, 'e.g. Position B'),
                const SizedBox(height: 40),
                if (provider.errorMessage != null) ...[
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(color: Colors.red[900]!.withOpacity(0.3), borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.red[800]!)),
                    child: Text(provider.errorMessage!, style: const TextStyle(color: Colors.red)),
                  ),
                  const SizedBox(height: 16),
                ],
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: provider.isCreatingSession ? null : _startDebate,
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.amber, foregroundColor: Colors.black, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
                    child: provider.isCreatingSession
                        ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                        : const Text('Start Debate', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  ),
                ),
                const SizedBox(height: 24),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(color: Colors.grey[900], borderRadius: BorderRadius.circular(10), border: Border.all(color: Colors.grey[800]!)),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('How it works', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Text('Each party submits arguments in turns. The neutral panel judge evaluates every claim against UN resolutions, Geneva Conventions, Rome Statute, and other binding international law. Points are awarded or deducted based on how well each claim aligns with established legal precedent.', style: TextStyle(color: Colors.grey[400], fontSize: 13, height: 1.5)),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildInput(TextEditingController controller, String hint) {
    return TextFormField(
      controller: controller,
      validator: (v) => v!.isEmpty ? 'Required' : null,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: TextStyle(color: Colors.grey[600]),
        filled: true,
        fillColor: Colors.grey[900],
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: Colors.grey[700]!)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: Colors.grey[700]!)),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: Colors.amber)),
      ),
    );
  }
}
