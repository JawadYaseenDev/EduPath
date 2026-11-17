import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../state/providers.dart';
import '../../widgets/common.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context).textTheme;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: ListView(padding: const EdgeInsets.all(24), shrinkWrap: true, children: [
              Center(child: Image.asset('assets/logo.png', height: 112, semanticLabel: 'EduRecommend logo')),
              const SizedBox(height: 16),
              Text('EduRecommend', textAlign: TextAlign.center, style: t.displaySmall),
              const SizedBox(height: 8),
              Text('Find universities and programmes in Pakistan that match your education, '
                  'budget and location.',
                  textAlign: TextAlign.center, style: t.bodyLarge),
              const SizedBox(height: 24),
              const _Point(Icons.fact_check_outlined,
                  'See where you meet the published admission requirements.'),
              const _Point(Icons.lightbulb_outline,
                  'Understand why each option is recommended, with the official source.'),
              const _Point(Icons.bookmark_border, 'Save options and compare fees, location and duration.'),
              const SizedBox(height: 16),
              const NoGuaranteeNote(),
              const SizedBox(height: 24),
              FilledButton(onPressed: () => context.go('/register'), child: const Text('Create account')),
              const SizedBox(height: 8),
              OutlinedButton(onPressed: () => context.go('/login'), child: const Text('Log in')),
              const SizedBox(height: 8),
              TextButton(
                  onPressed: () => context.go('/explore'),
                  child: const Text('Browse universities without an account')),
            ]),
          ),
        ),
      ),
    );
  }
}

class _Point extends StatelessWidget {
  const _Point(this.icon, this.text);
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(children: [
          Icon(icon, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: 12),
          Expanded(child: Text(text)),
        ]),
      );
}

class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({super.key, required this.register});
  final bool register;

  @override
  ConsumerState<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends ConsumerState<AuthScreen> {
  final _form = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _accepted = false;
  bool _busy = false;
  bool _hidePassword = true;
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _error = null);
    if (!_form.currentState!.validate()) return;
    if (widget.register && !_accepted) {
      setState(() => _error = 'Please accept the terms and privacy policy to continue.');
      return;
    }
    setState(() => _busy = true);
    try {
      final auth = ref.read(authProvider.notifier);
      if (widget.register) {
        await auth.register(_email.text.trim(), _password.text, _name.text.trim());
        if (mounted) context.go('/setup');
      } else {
        await auth.login(_email.text.trim(), _password.text);
        if (mounted) context.go('/home');
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final register = widget.register;
    return Scaffold(
      appBar: AppBar(
        title: Text(register ? 'Create account' : 'Log in'),
        leading: BackButton(onPressed: () => context.go('/welcome')),
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Form(
            key: _form,
            autovalidateMode: AutovalidateMode.onUserInteraction,
            child: ListView(padding: const EdgeInsets.all(20), children: [
              if (register) ...[
                TextFormField(
                  controller: _name,
                  decoration: const InputDecoration(labelText: 'Full name'),
                  textCapitalization: TextCapitalization.words,
                  autofillHints: const [AutofillHints.name],
                  validator: (v) =>
                      (v ?? '').trim().length < 2 ? 'Please enter your full name.' : null,
                ),
                const SizedBox(height: 16),
              ],
              TextFormField(
                controller: _email,
                decoration: const InputDecoration(labelText: 'Email address'),
                keyboardType: TextInputType.emailAddress,
                autofillHints: const [AutofillHints.email],
                validator: (v) => RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch((v ?? '').trim())
                    ? null
                    : 'Please enter a valid email address.',
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _password,
                obscureText: _hidePassword,
                autofillHints: [register ? AutofillHints.newPassword : AutofillHints.password],
                decoration: InputDecoration(
                  labelText: 'Password',
                  helperText: register ? 'At least 8 characters.' : null,
                  suffixIcon: IconButton(
                    tooltip: _hidePassword ? 'Show password' : 'Hide password',
                    icon: Icon(_hidePassword ? Icons.visibility : Icons.visibility_off),
                    onPressed: () => setState(() => _hidePassword = !_hidePassword),
                  ),
                ),
                validator: (v) {
                  if ((v ?? '').isEmpty) return 'Please enter your password.';
                  if (register && v!.length < 8) return 'Password must be at least 8 characters.';
                  return null;
                },
                onFieldSubmitted: (_) => _submit(),
              ),
              if (register)
                CheckboxListTile(
                  value: _accepted,
                  onChanged: (v) => setState(() => _accepted = v ?? false),
                  contentPadding: EdgeInsets.zero,
                  controlAffinity: ListTileControlAffinity.leading,
                  title: const Text('I accept the terms of use and privacy policy.'),
                ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                InfoBanner(_error!, icon: Icons.error_outline, warning: true),
              ],
              const SizedBox(height: 20),
              FilledButton(
                onPressed: _busy ? null : _submit,
                child: _busy
                    ? const SizedBox(
                        width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : Text(register ? 'Create account' : 'Log in'),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => context.go(register ? '/login' : '/register'),
                child: Text(register
                    ? 'Already have an account? Log in'
                    : 'New here? Create an account'),
              ),
            ]),
          ),
        ),
      ),
    );
  }
}
