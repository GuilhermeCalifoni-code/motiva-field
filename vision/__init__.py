"""Bloco 2 — visao computacional do MOTIVA-FIELD.

Existe para permitir `python -m vision.calibracao` e `python -m vision.conferir`
a partir da raiz da worktree.

Os modulos tambem continuam executaveis de dentro de vision/ (`python
teste_sintetico.py`), entao os imports entre eles tentam a forma relativa
primeiro e caem na plana quando nao ha pacote pai.
"""
