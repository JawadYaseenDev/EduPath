import 'package:material_ui/material_ui.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/format.dart';
import '../core/theme.dart';
import '../data/models.dart';

/// Eligibility status: icon + colour + words (never colour alone).
class StatusChip extends StatelessWidget {
  const StatusChip(this.category, {super.key, this.dense = false});
  final String category;
  final bool dense;

  static (IconData, String) describe(String category) => switch (category) {
        'eligible' => (Icons.check_circle, 'Eligible'),
        'potentially_eligible' => (Icons.help, 'Potentially eligible'),
        _ => (Icons.cancel, 'Not currently eligible'),
      };

  static Color colour(BuildContext context, String category) {
    final s = Theme.of(context).colorScheme;
    return switch (category) {
      'eligible' => StatusColors.eligible(s),
      'potentially_eligible' => StatusColors.potentially(s),
      _ => StatusColors.notEligible(s),
    };
  }

  @override
  Widget build(BuildContext context) {
    final (icon, label) = describe(category);
    final colour = StatusChip.colour(context, category);
    return Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(icon, color: colour, size: dense ? 16 : 20),
      const SizedBox(width: 4),
      Flexible(
        child: Text(label,
            style: (dense
                    ? Theme.of(context).textTheme.labelMedium
                    : Theme.of(context).textTheme.labelLarge)
                ?.copyWith(color: colour, fontWeight: FontWeight.w600)),
      ),
    ]);
  }
}

class OutcomeIcon extends StatelessWidget {
  const OutcomeIcon(this.outcome, {super.key});
  final String outcome;

  @override
  Widget build(BuildContext context) {
    final s = Theme.of(context).colorScheme;
    final (icon, colour, label) = switch (outcome) {
      'pass' => (Icons.check_circle_outline, StatusColors.eligible(s), 'Met'),
      'fail' => (Icons.highlight_off, StatusColors.notEligible(s), 'Not met'),
      _ => (Icons.help_outline, StatusColors.potentially(s), 'Needs checking'),
    };
    return Semantics(label: label, child: Icon(icon, color: colour, size: 22));
  }
}

/// Fictional sample data must never look like real data.
class DemoBadge extends StatelessWidget {
  const DemoBadge({super.key});

  @override
  Widget build(BuildContext context) {
    final s = Theme.of(context).colorScheme;
    return Tooltip(
      message: 'Sample data for testing. This is not a real university.',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: BoxDecoration(
            color: s.tertiaryContainer, borderRadius: BorderRadius.circular(6)),
        child: Text('SAMPLE DATA',
            style: Theme.of(context)
                .textTheme
                .labelSmall
                ?.copyWith(color: s.onTertiaryContainer, fontWeight: FontWeight.w700)),
      ),
    );
  }
}

class InfoBanner extends StatelessWidget {
  const InfoBanner(this.text, {super.key, this.icon = Icons.info_outline, this.warning = false});
  final String text;
  final IconData icon;
  final bool warning;

  @override
  Widget build(BuildContext context) {
    final s = Theme.of(context).colorScheme;
    final bg = warning ? s.errorContainer : s.secondaryContainer;
    final fg = warning ? s.onErrorContainer : s.onSecondaryContainer;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(12)),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, color: fg, size: 20),
        const SizedBox(width: 10),
        Expanded(child: Text(text, style: TextStyle(color: fg))),
      ]),
    );
  }
}

/// BASE-02: recommendations support decisions; they do not guarantee admission.
class NoGuaranteeNote extends StatelessWidget {
  const NoGuaranteeNote({super.key});

  @override
  Widget build(BuildContext context) => const InfoBanner(
        'Meeting the minimum requirements does not guarantee admission. Final selection '
        'depends on merit, available seats and the university. Always confirm on the '
        'official website.',
      );
}

class ErrorView extends StatelessWidget {
  const ErrorView(this.error, {super.key, this.onRetry});
  final Object error;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(Icons.cloud_off, size: 48, color: Theme.of(context).colorScheme.outline),
            const SizedBox(height: 12),
            Text(error.toString(), textAlign: TextAlign.center),
            if (onRetry != null) ...[
              const SizedBox(height: 12),
              OutlinedButton.icon(
                  onPressed: onRetry, icon: const Icon(Icons.refresh), label: const Text('Try again')),
            ],
          ]),
        ),
      );
}

class Loading extends StatelessWidget {
  const Loading({super.key});
  @override
  Widget build(BuildContext context) => const Center(child: CircularProgressIndicator());
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key, this.trailing});
  final String text;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 20, bottom: 8),
        child: Row(children: [
          Expanded(child: Text(text, style: Theme.of(context).textTheme.titleMedium)),
          ?trailing,
        ]),
      );
}

class OfferingTile extends StatelessWidget {
  const OfferingTile(this.card, {super.key, this.category, this.onTap, this.trailing, this.footer});
  final OfferingCard card;
  final String? category;
  final VoidCallback? onTap;
  final Widget? trailing;
  final Widget? footer;

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context).textTheme;
    final s = Theme.of(context).colorScheme;
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(card.programmeTitle, style: t.titleMedium),
                  const SizedBox(height: 2),
                  Text(card.universityName, style: t.bodyMedium),
                  Text('${card.campusName} · ${card.city}',
                      style: t.bodySmall?.copyWith(color: s.onSurfaceVariant)),
                ]),
              ),
              ?trailing,
            ]),
            const SizedBox(height: 10),
            Wrap(spacing: 6, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center, children: [
              if (category != null) StatusChip(category!, dense: true),
              if (card.isDemo) const DemoBadge(),
              _Fact(Icons.account_balance, sectorLabel(card.sector)),
              _Fact(Icons.payments_outlined,
                  '${pkr(card.chargesPerSemester)}${card.chargesPerSemester != null ? '/sem' : ''}'
                  '${card.feeIsEstimated ? ' (est.)' : ''}'),
              if (card.hostelFor.isNotEmpty) const _Fact(Icons.hotel_outlined, 'Hostel'),
              if (card.entryTests.isNotEmpty) _Fact(Icons.edit_note, card.entryTests.join(', ')),
              if (card.genderPolicy != 'coeducation')
                _Fact(Icons.wc, genderPolicyLabel(card.genderPolicy)),
              if (card.isStale) _Fact(Icons.history, 'Data from ${card.cycleLabel}', warn: true),
            ]),
            ?footer,
          ]),
        ),
      ),
    );
  }
}

class _Fact extends StatelessWidget {
  const _Fact(this.icon, this.text, {this.warn = false});
  final IconData icon;
  final String text;
  final bool warn;

  @override
  Widget build(BuildContext context) {
    final s = Theme.of(context).colorScheme;
    final colour = warn ? s.error : s.onSurfaceVariant;
    return Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(icon, size: 15, color: colour),
      const SizedBox(width: 3),
      Text(text, style: Theme.of(context).textTheme.labelMedium?.copyWith(color: colour)),
    ]);
  }
}

Future<void> openLink(BuildContext context, String? url) async {
  if (url == null) return;
  final ok = await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
  if (!ok && context.mounted) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text('Could not open $url')));
  }
}

void showMessage(BuildContext context, String message) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(message)));
}
