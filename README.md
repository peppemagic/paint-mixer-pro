# paint-mixer-pro
Advanced pigment mixing tool for digital &amp; traditional painting. Supports Kubelka-Munk &amp; subtractive models.
## 🎨 Paint Mixer Pro v6.5 Final

**Strumento avanzato di miscelazione colori per pittura digitale e fisica.**

Paint Mixer Pro è un software professionale sviluppato da **Giuseppe Luongo**, progettato per artisti, pittori e restauratori. Permette di calcolare ricette di miscelazione precise simulando la fisica della luce e del pigmento su diversi supporti (carta, tela, gesso, ecc.).

## 🚀 Caratteristiche Principali
*   **Doppio Motore di Calcolo:**
    *   *Empirico (Sottrattivo):* Algoritmo ponderato veloce.
    *   *Kubelka-Munk (Scientifico):* Calcolo avanzato di assorbimento (K) e scattering (S) della luce per risultati ultra-realistici.
*   **Simulazione Supporti:** Impatto reale del fondo (es. Arches, Canson, Lino) sulla resa del colore.
*   **Auto-Mix Intelligente:** Clicca un punto sulla ruota colori e il software trova la ricetta ottimale tra i pigmenti disponibili.
*   **Database JSON:** Gestione completa di pigmenti, opacità e fattori tintoriali tramite file configurabile.
*   **Compatibilità:** Testato su Linux (Mint/Ubuntu) e Windows.

## 🛠 Requisiti
Il software richiede **Python 3.8+** e le seguenti librerie:
*   `PyQt5` (Interfaccia grafica)
*   `colormath` (Calcolo scientifico colori)
*   `Pillow` (Elaborazione immagini ruota colori)
*   `scipy` (Ottimizzazione matematica)
*   `numpy`

### Installazione rapida
```bash
pip install PyQt5 colormath Pillow scipy numpy

## Credits & Acknowledgements

* **Color Wheel:** The color wheel image (`cwheel06.gif`) is property of **Bruce MacEvoy** ([handprint.com](https://www.handprint.com)). It is used here in good faith for educational, non-commercial, and artistic visualization purposes.
* **Color Math:** Built using the `colormath` library for CIE LAB color space calculations.

Sviluppato da Giuseppe Luongo.
========================================================================
NOTE LEGALI E LICENZA D'USO
========================================================================

SOFTWARE: Paint Mixer Pro v6.5 Final
AUTORE: Giuseppe Luongo
COPYRIGHT: © 2024-2026 Giuseppe Luongo

1. LICENZA
Questo software è rilasciato sotto licenza GNU General Public License v3.0 (GPL v3). 
Ciò significa che sei libero di utilizzare, studiare e modificare il programma, 
a patto di mantenere intatto il riferimento al… la resa fisica su tela o carta, poiché 
questa dipende da variabili esterne (umidità, spessore del film, qualità dei 
pigmenti grezzi). L'utilizzo del software è a totale rischio dell'utente.
L'autore non è responsabile per danni diretti o indiretti derivanti dall'uso.

3. ATTRIBUZIONE
Ogni copia, modifica o derivato di questo software deve riportare chiaramente:
"Basato su Paint Mixer Pro, sviluppato da Giuseppe Luongo".

========================================================================
