# Progetto Uniform Coloring
Uniform Coloring è un dominio in cui si ha una griglia rettangolare di celle colorate (B=blu, Y=yellow, G=green) e una testina colorante (T). La testina può:
- **Spostarsi** nelle 4 direzioni cardinali (N, S, E, W) con costo 1
- **Colorare** la cella corrente con un colore disponibile a costi differenziati: cost(B)=1, cost(Y)=2, cost(G)=3

**Obiettivo**: colorare tutte le celle dello stesso colore e riportare la testina nella posizione iniziale.

---
## 1. Descrizione Formale del Dominio

- Griglia rettangolare di dimensione $R \times C$
- Ogni cella $(r, c)$ ha un colore $\in \{B, Y, G\}$, oppure contiene la testina $T$ (che non ha colore proprio)
- La testina occupa esattamente una cella alla volta

### Stato
Uno stato è una tripla $(r_T, c_T, \text{grid})$ dove:
- $(r_T, c_T)$ è la posizione corrente della testina
- $\text{grid}$ è una tupla di $R \times C$ colori che rappresenta la colorazione di tutte le celle
- La cella di partenza $(r_0, c_0)$ non ha un colore proprio (è identificata da $T$) e non può mai essere colorata dall'agente

### Azioni
| Azione | Precondizione | Effetto | Costo |
|--------|--------------|---------|-------|
| NORTH | $r_T > 0$ | $r_T \leftarrow r_T - 1$ | 1 |
| SOUTH | $r_T < R - 1$ | $r_T \leftarrow r_T + 1$ | 1 |
| WEST | $c_T > 0$ | $c_T \leftarrow c_T - 1$ | 1 |
| EAST | $c_T < C - 1$ | $c_T \leftarrow c_T + 1$ | 1 |
| COL_B | Sempre | $\text{grid}[r_T][c_T] \leftarrow B$ | 1 |
| COL_Y | Sempre | $\text{grid}[r_T][c_T] \leftarrow Y$ | 2 |
| COL_G | Sempre | $\text{grid}[r_T][c_T] \leftarrow G$ | 3 |

### Vincoli
- **V1**: L'agente compie un solo passo alla volta
- **V2**: L'agente si può muovere solo fra celle adiacenti (4-connessione cardinale)
- **V3**: L'agente non può uscire dalla griglia
- **V4**: L'agente può colorare solo la cella in cui si trova
- **V5**: L'agente può colorare la cella con qualsiasi colore disponibile, anche lo stesso colore già presente
- **V6**: L'agente non può colorare la cella di partenza $(r_0, c_0)$

### Goal Test
Uno stato è goal se:
1. Tutte le celle della griglia, **esclusa la cella di partenza** $(r_0, c_0)$, hanno lo **stesso colore**
2. La testina si trova nella **posizione iniziale** $(r_0, c_0)$