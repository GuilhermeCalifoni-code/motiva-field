# modelos

O classificador treinado mora aqui. O arquivo em si **nao e versionado** —
e binario grande e muda a cada retreino. Só este README entra no git.

## Arquivo esperado

```
vision/modelos/mobilenet_motiva.keras
```

Para usar outro caminho, defina a variavel de ambiente:

```bash
MOTIVA_MODELO=/caminho/para/outro.keras
```

## Ao exportar do Colab

O `/content` do Colab e volatil: o que fica so ali se perde ao encerrar a
sessao. Baixe o arquivo antes de fechar o notebook.

```python
model.save("mobilenet_motiva.keras")
from google.colab import files
files.download("mobilenet_motiva.keras")
```

## Confira a ordem das classes ao exportar

O Keras ordena os diretorios de classe alfabeticamente, entao a ordem das
saidas depende de como as pastas foram nomeadas — nao do que parece logico.
Anote o resultado de:

```python
print(train_generator.class_indices)
```

Se a ordem nao for `Seguro, Atenção, Crítico`, ajuste `CLASSES_PADRAO` em
`classificacao.py` ou defina:

```bash
MOTIVA_CLASSES="Atenção,Crítico,Seguro"
```

Um desalinhamento aqui nao levanta erro: so troca os rotulos em silencio, e
"Crítico" passa a ser reportado como "Seguro".

## Pre-processamento

A inferencia replica exatamente a cadeia do treino, incluindo a dupla
normalizacao. Ver a docstring de `preprocessar` em `classificacao.py`. Se o
treino mudar essa cadeia, `classificacao.py` precisa mudar junto.
