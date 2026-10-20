# Motiva Field — Mobile

Aplicativo Flutter usado pela equipe de campo do Motiva Field.

## Fluxo principal

Login → visão geral → ordem ativa → deslocamento → chegada → comprovação → validação.

A comprovação exige evidências antes do envio. O aplicativo também possui uma área de inteligência por imagem e tenta sincronizar a operação com o backend quando disponível.

## Executar

```bash
flutter pub get
flutter run
```

## Qualidade

```bash
flutter analyze
flutter test
```

## APK

```bash
flutter build apk --release
```

Saída:

```text
build/app/outputs/flutter-apk/app-release.apk
```

A Sprint 4 também possui build automatizado em `.github/workflows/build-apk.yml`.
