# Ponderada CC08 - Pulseira Tato

Aluno: Messias Olivindo

Repositório com o código e o relatório da ponderada CC08 da pulseira Tato.

## Como rodar a questão A4 (produtor/consumidor com buffer circular)

Requer Python 3 (somente biblioteca padrão). Cada versão faz 3 execuções em sequência com N = 3 e 20.000 amostras.

```
cd ponderada/codigo && python3 versao1.py
cd ponderada/codigo && python3 versao2.py
cd ponderada/codigo && python3 versao3.py
```

Cada versão imprime um cabeçalho (versão, N, amostras) e, por execução, uma linha:

`RESULTADO versao=<v> execucao=<k> produzidas=<n> consumidas=<n> perdidas=<n> duplicadas=<n> travou=<sim|nao>`

- `versao1.py`: sem sincronização (contador compartilhado e espera ocupada). Espera-se perda/duplicação de amostras e, às vezes, travamento. É lenta (cerca de 2 min por execução).
- `versao2.py`: com semáforos vazio, cheio e mutex. Espera-se 20000 consumidas, 0 perdidas, 0 duplicadas, sem travar.
- `versao3.py`: produtor com wait(mutex) antes de wait(vazio). Espera-se deadlock (travou=sim) quando o buffer enche.
