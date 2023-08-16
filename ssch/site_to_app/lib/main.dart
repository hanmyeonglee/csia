import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Image(
              image: AssetImage(
                "image/SSCHLogo.reduct.png",
              ),
              height: 10,
            ),
          ],
        ),
      ),
      body: FutureBuilder(
          future: openURL(),
          builder: (context, snapshot) {
            if (snapshot.hasData) {
              return snapshot.requireData;
            } else {
              return const Text("Sorry, Something went wrong...");
            }
          }),
    );
  }

  Future<Widget> openURL() async {
    final uri = Uri.parse("http://csia.hs.kr");
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
      return const Icon(
        Icons.favorite,
        size: 50,
      );
    } else {
      return const Icon(
        Icons.wifi_off_outlined,
        size: 50,
      );
    }
  }
}
