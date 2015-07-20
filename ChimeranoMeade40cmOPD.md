Como rodar o chimera no Meade 40cm LNA

# Introdução #

A idéia deste documento é explicar como usar o telescópio Meade 40cm no OPD.


# Início #

Este é um telescópio como qualquer outro.  Faça as coisas normais:

  * Certifique-se que a umidade é baixa e que a cúpula pode ser aberta.
  * Se o telescópio estiver ligado, deixe-o ligado, ele deve permanecer ligado o tempo inteiro.
  * SE e SOMENTE SE o telescópio estiver desligado coloque-o em ângulo horário = ZERO e declinação = ZERO.  Ligue o telescópio.
  * O telescópio deve estar apontando razoavelmente bem.  Se não estiver cale o telescópio usando o manual da MEADE (vou transcrever essas instruções pra cá depois).
  * Conexões
    1. Telescópio computador linux - serial
    1. Focador NGF-S computador linux - serial
    1. Cúpula computador linux - serial
    1. Câmera computador linux - USB
  * Certifique-se que tudo está conectado e ligado.
  * Pelo computador (veja abaixo) abra a cúpula
  * Remova a tampa do telescópio. (sempre depois de abrir a cúpula - se algum urubu fez caca na cúpula não cai no telescópio aberto :-)

# No computador #


Evite ao máximo mexer nas coisas via manetes.  Faça tudo pelo computador.

Logue-se como obs / senha?

Abra o ambiente gráfico X11:

```
startx
```

abra um terminal tipo xterm, kterm, konsole (aperte Alt-F2 e digite xterm ou  kterm ou  konsole.

Verifique se o chimera já não está rodando:

```
ps aux | grep chimera
```

Se houver algum processo do chimera rodando mate-o com "kill -9"

```
kill -9 666
```

666 é um número hipotético, substitua-o pelo número do chimera que aparecer.

Inicie o chimera:

```
chimera -vv
```

Abra outro terminal.

Dentro do novo terminal certifique-se que está tudo funcionando:

```
  > chimera-dome --info
  > chimera-tel --info
  > chimera-cam --info
  > chimera-focus --info
```

Mensagens de erro em qualquer um dos quatro normalmente significa cabo desconectado, aparelho desligado, etc.

Cada um desses comandos "chimera-qualquercoisa" tem uma opção --help que lista todas opções do comando.  Elas estão razoavelmente bem explicadas e são mais ou menos óbvias.

Resfrie a câmera:

```
chimera-cam -T 0
```

Para começo de conversa, abra a cúpula:

```
chimera-dome --open
```

Avise a cúpula para acompanhar o telescópio:

```
chimera-dome --track
```

Comece apontando o telescópio para algum objeto óbvio:

```
chimera-tel --slew --object m6
```

qualquer uma das três formas abaixo vai levá-lo a Antares:

```
> chimera-tel --slew --object antares
> chimera-tel --slew --ra 16:29:24.4609 --dec -26:25:55.209 
> chimera-tel --slew --ra "16 29 24.4609" --dec "-26 25 55.209" 
```

Se o telescópio não estiver apontando direito:

Peça para alguém olhar pela buscadora e centrar o objeto (usando a manete) desejado na buscadora (é bom fazer isso com alfa-estrelas, como Antares, Arturus, etc), depois de centrado o tal obscuro objeto tire uma imagem com o CCD, o objeto deve estar lá, se estiver no CCD:

```
chimera-tel --sync --object antares
```

Com isto o sistema passa a pensar que as coordenadas que ele tem são as coordenadas do objeto especificado pelo comando sync acima.

use aspas para objetos com nomes compostos:

```
chimera-tel --slew --object "QS Vir" 
```



depois que o telescópio apontar tire uma imagem:

```
chimera-cam -t 30 --filter R

(as imagens tiradas são colocadas por default em ~/images/yyyymmdd/yyyymmddhhmm-NNNN.fits)
```

o filtro R é recomendado para objetos mais fracos como M6 por estar no pico de sensibilidade do CCD.  Se apontar para Antares: -t 0.1 --filter B

Agora está na hora de fazer o foco.  Esta é uma boa razão para apontar para M6 e não Antares:

```
chimera-focus --auto --range=0-7000 --step 500 --exptime=10 --filter=R 
```

  * auto - o sistema fará uma sessão completa de autofoco
  * range - significa que o sistema vai mudar o foco de 0 a 7000 (o intervalo completo do NGF-S)
  * step - o tamanho do passo entre cada tentativa
  * exptime - o tempo de exposição de cada imagem de foco
  * filter - o filtro usado (sempre bom usar o R)

Ao final desta sessão chimera-focus escolherá o melhor foco.  Normalmente haverá alguns pontos ruins nos extremos do intervalo.  É bom refinar a busca pelo foco no final.  Suponha que o foco escolhido foi 4344.  Refaça o foco:

```
> chimera-focus --auto --range=3800-4800 --step 100 --exptime=10 --filter=R 
```

Ajuste os números a seu gosto e ache o jeito mais perfeito e mais rápido de fazer o foco.  Lembre exposições de foco não devem ser mais curtas que 5s, jamais.

Às vezes pode que o algoritmo de foco se atrapalhe com muitos pontos ruins perto de 0 ou perto de 7000.  Quando isso acontecer restrinja a "range" para aquela região melhor, perto de onde os valores de FWHM mostradas na tela são mais razoáveis.

Agora para calar o telescópio:

```
chimera-tel --slew --object m6
chimera-pverify --here
```

`chimera-pverify` irá tirar uma imagem onde o telescópio está (em M6 no caso), calcular o WCS (astrometria) da imagem obtida pela câmera e comparar com as coordenadas do telescópio.  Se necessário irá mover o telescópio até que as coordenadas do centro da imagem sejam iguais às coordenadas pedidas quando apontamos o telescópio (ou seja quando as coordenadas do centro da imagem forem iguais às coordenadas de M7 - dentro da tolerância default de 1 minuto de arco).

Quando terminar cale o telescópio:

```
chimera-tel --sync --object m6
```



Daqui para frente tudo se resume a apontar o telescópio (chimera-tel) e tirar imagens (chimera-cam).

Quando cansar:

```
> chimera-tel --park
```

isto estaciona o telescópio, deixa-o ligado e desliga o acompanhamento.  O telescópio deve ficar LIGADO, desta forma não se perde o apontamento.

```
> chimera-dome --close
> chimera-dome --to=AZIMUTE_ONDE_NAO_CHOVE
```

fecha a cupula e estaciona.

```
> chimera-cam --stop-cooling
```

desliga o resfriamento da câmera.

Coloque a tampa no telescópio e vá dormir.

# Problemas #

# Às vezes as coisas ficam meio bobas.  Pode ter mais de um chimera rodando.  Pare tudo. Mate todos chimeras:

# killall chimera

# Às vezes a cúpula pira.  Alguém precisa reiniciar a cúpula, tirando-a e colocando-a de volta na tomada.

# Se tudo está pirado reinicie tudo.