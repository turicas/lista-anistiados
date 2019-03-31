# Lista de Anistiados

Script que extrai lista de beneficiados da [lei da anistia
(10.559/2002)](http://www.planalto.gov.br/ccivil_03/leis/2002/L10559.htm) dos
arquivos PDF disponibilizados em 2015 e 2018 e gera um CSV para cada ano.


## Licença

A licença do código é [LGPL3](https://www.gnu.org/licenses/lgpl-3.0.en.html). e
dos dados [Creative Commons Attribution
ShareAlike](https://creativecommons.org/licenses/by-sa/4.0/). Caso utilize os
dados, cite a fonte original e quem tratou os dados, como: **Fonte: Ministério
da Justiça, dados tratados por Álvaro Justen/[Brasil.IO](https://brasil.io/)**.
Caso compartilhe os dados, utilize a mesma licença.


## Dados

Caso não queira rodar o script, [baixe os dados
diretamente](https://drive.google.com/open?id=1HWR9WxqqXoapfx1Ki_HfEzl8kpoAraMT).



## Instalando

Para instalar as dependências você precisa de Python 3.7 em sua máquina.
Execute:

```bash
pip install -r requirements.txt
```


## Rodando

Os arquivos originais não estão mais disponíveis e você precisará baixá-los de
outra fonte. [Leia essa thread no
Twitter](https://twitter.com/turicas/status/1112491956314259457) para mais
detalhes.

```bash
python extrai_anistiados.py
```
