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


---
## 2. Ricerca nello Spazio degli Stati

### 2.1 Dimensione dello spazio
Per una griglia $R \times C$ la testina può occupare $R \cdot C$ posizioni. Ogni cella (esclusa la cella di partenza) può assumere uno dei 3 colori, ma le azioni di colorazione applicano **solo** il `target_color` scelto in fase di inizializzazione: una cella quindi transita esclusivamente dal suo colore iniziale a `target_color`, mai verso gli altri due. Gli stati **raggiungibili** sono perciò

$$|S_{\text{raggiungibili}}| \approx (R \cdot C) \cdot 2^{w}$$

dove $w$ è il numero di celle inizialmente diverse dal target (celle "sbagliate"). Il fattore di ramificazione è ≤ 5 (fino a 4 movimenti + 1 colorazione). La crescita è **esponenziale in $w$**: è $w$, non il numero di celle, a determinare la trattabilità.

### 2.2 Algoritmi
- **BFS** (`breadth_first_graph_search`): ottimale solo a costi uniformi; qui i colori hanno costi 1/2/3, quindi minimizza i **passi**, non il costo.
- **UCS** (`uniform_cost_search`): ottimale sul costo totale. Lazy deletion sull'heap.
- **A\*** (`astar_search`): ottimale con euristica ammissibile. Quattro euristiche testate:
  - `color` = celle_sbagliate × costo_target (ignora i movimenti)
  - `color_nearest_distance` = costo colorazione + andata/ritorno alla cella sbagliata più vicina
  - `mst` = costo colorazione + MST (Prim) su {testina, celle sbagliate, start} — lower bound del TSP
  - `ideal` = costo colorazione + tour TSP esatto (brute-force $w!$, solo $w \le 8$)

### 2.3 Prestazioni misurate
Griglie casuali (seed fisso), testina nell'angolo in basso a sinistra, `target` scelto automaticamente. Cap di **400 000 nodi espansi** per esecuzione (≈ limite pratico di tempo/memoria). `exp` = nodi espansi, `front` = frontiera massima, `t` = tempo.

| Griglia | celle | $w$ | stati ragg. | BFS | UCS | A\* color | A\* nearest | A\* MST | A\* ideal |
|---------|-------|-----|-------------|-----|-----|-----------|-------------|---------|-----------|
| 2×2 | 4 | 1 | 8 | 6 / 0.00s | 7 | 7 | 7 | 6 | 6 |
| 3×3 | 9 | 4 | 144 | 142 / 0.01s | 143 | 142 | 72 | **55** | 39 |
| 3×4 | 12 | 6 | 768 | 752 / 0.03s | 767 | 732 | 217 | **44** | 23 |
| 4×4 | 16 | 9 | 8 192 | 8 163 / 0.43s | 8 183 | 8 176 / 1.1s | 3 877 | **236 / 0.16s** | n/d ($w>8$) |
| 4×5 | 20 | 13 | 163 840 | 163 836 / 13s | 163 839 / 15s | 163 781 / 21s | 97 282 / 15s | **803 / 0.66s** | n/d |
| 5×5 | 25 | 22 | ~1.0×10⁸ | CAP / 36s | CAP / 52s | CAP / 101s | CAP / 113s | **6 049 / 11s** | n/d |
| 5×6 | 30 | 18 | ~7.9×10⁶ | CAP / 29s | CAP / 38s | CAP / 86s | — | — | n/d |

(I valori `exp` sono i nodi espansi; in **grassetto** il vincitore. "CAP" = superato il limite di 400 000 espansioni senza soluzione.)

### 2.4 Problemi risolti / irrisolti
- **BFS, UCS, A\* `color`** espandono di fatto l'intero spazio raggiungibile (`exp` ≈ stati raggiungibili): l'euristica `color` è troppo debole (trascura i movimenti) e non riduce praticamente nulla. Limite pratico: **≈ 4×5 / $w \le 13$** (~160k stati, ~15–20 s). Da 5×5 in su **saturano il cap** senza trovare soluzione.
- **A\* `color_nearest_distance`** taglia 2–4×: estende il limite di poco, sempre attorno a $w \approx 13$; a 5×5 satura anche lei.
- **A\* `mst`** è nettamente la migliore: lower bound del TSP molto informativo e consistente. Risolve **5×5 (22 celle sbagliate, ~10⁸ stati raggiungibili) espandendo solo 6 049 nodi in 11 s**, dove tutte le altre saturano. È l'unica che scala oltre $w = 13$.
- **A\* `ideal`** espande il minor numero di nodi in assoluto (TSP esatto), ma il costo per-nodo è $O(w!)$: utilizzabile **solo per $w \le 8$** (fino a ~3×4). Oltre, il calcolo dell'euristica esplode prima dello spazio degli stati.

### 2.5 Dimensione dei problemi risolti
La trattabilità dipende da $w$ (celle sbagliate), non dalla dimensione della griglia:

| Algoritmo | Limite pratico (≤ ~15 s, ≤ 400k espansi) |
|-----------|-------------------------------------------|
| BFS / UCS / A\* `color` | $w \lesssim 13$ (fino a ~4×5) |
| A\* `color_nearest_distance` | $w \lesssim 13$ |
| A\* `mst` | $w \gtrsim 22$ (5×5 e oltre) — **scelta di default** |
| A\* `ideal` | $w \le 8$ (per limite dell'euristica, non dello spazio) |

In sintesi: A\* con euristica `mst` è il solver di riferimento; le griglie tipiche riconosciute da immagine (≤ 4×4) sono risolte in modo ottimo e quasi istantaneo da tutti gli algoritmi, mentre per griglie più grandi solo `mst` resta praticabile.


# Modelli AI

Il dataset su cui basiamo i vari modelli testati è EMNIST Balanced, composto da 131.600 immagini, suddivise in 112.800 per il training e 18.800 per il test.

Le immagini hanno dimensione 28×28 pixel e contengono le cifre da 0 a 9, tutte le 26 lettere dell’alfabeto latino in maiuscolo e 11 lettere in minuscolo la cui forma è sostanzialmente diversa da quella delle corrispondenti lettere maiuscole.

Di queste abbiamo selezionato solamente le lettere B, b, G, g, T, t, Y e y, creando due versioni del dataset: una contenente esclusivamente le lettere maiuscole e una comprendente anche le corrispondenti lettere minuscole.

Per la classificazione delle immagini sono stati realizzati e confrontati due modelli di reti neurali: il primo basato su una rete neurale Multilayer Perceptron (MLP) e il secondo su una rete neurale convoluzionale (CNN). Entrambi 

