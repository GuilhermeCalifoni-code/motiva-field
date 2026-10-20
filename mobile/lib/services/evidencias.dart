import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';

class RegistroLocalizacao {
  const RegistroLocalizacao({
    required this.latitude,
    required this.longitude,
    required this.precisaoM,
  });

  final double latitude;
  final double longitude;
  final double precisaoM;
}

abstract class EvidenciasGateway {
  Future<String?> capturarFoto();
  Future<RegistroLocalizacao> obterLocalizacao();
}

class EvidenciasPluginGateway implements EvidenciasGateway {
  EvidenciasPluginGateway({ImagePicker? imagePicker})
      : _imagePicker = imagePicker ?? ImagePicker();

  final ImagePicker _imagePicker;

  @override
  Future<String?> capturarFoto() async {
    final XFile? foto = await _imagePicker.pickImage(
      source: ImageSource.camera,
      imageQuality: 85,
      preferredCameraDevice: CameraDevice.rear,
    );
    return foto?.path;
  }

  @override
  Future<RegistroLocalizacao> obterLocalizacao() async {
    final bool servicoAtivo = await Geolocator.isLocationServiceEnabled();
    if (!servicoAtivo) {
      throw StateError(
        'Ative a localização do aparelho para registrar a evidência.',
      );
    }

    LocationPermission permissao = await Geolocator.checkPermission();
    if (permissao == LocationPermission.denied) {
      permissao = await Geolocator.requestPermission();
    }
    if (permissao == LocationPermission.denied) {
      throw StateError('Permissão de localização negada.');
    }
    if (permissao == LocationPermission.deniedForever) {
      throw StateError(
        'A localização foi bloqueada. Libere a permissão nas configurações.',
      );
    }

    final Position posicao = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
      ),
    );

    return RegistroLocalizacao(
      latitude: posicao.latitude,
      longitude: posicao.longitude,
      precisaoM: posicao.accuracy,
    );
  }
}

EvidenciasGateway evidenciasGateway = EvidenciasPluginGateway();
