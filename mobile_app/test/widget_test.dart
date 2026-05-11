import 'package:flutter_test/flutter_test.dart';
import 'package:subwaybev_mobile/main.dart';

void main() {
  testWidgets('MetroEyes app smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const MetroEyesApp());
    expect(find.byType(MetroEyesApp), findsOneWidget);
  });
}
