---
name: Phase 0B — Skinfold-Formel-Fallstrick
description: JP11-Konstanten (3-Punkt-JP) erzeugen bei 11 Messpunkten unrealistische Ergebnisse — Pařízkova verwenden.
---

# Skinfold-Körperfett: Fallstrick bei 11-Punkt-Methode

## Die Regel
Für **11-Punkt-Hautfalten** die **Pařízkova (1977)**-Logarithmenformel verwenden, NICHT die Jackson-Pollock-Polynomkonstanten.

**Warum:** Die JP-Polynomkonstanten (z. B. 1.10938 − 0.0008267 × Σ) stammen aus der JP-3-Punkt-Gleichung. Auf 11 Punkte (Σ ≈ 120–200 mm) angewendet erzeugen sie %KF > 30 % bei Sportlern mit normalem Körperfettanteil — völlig unplausibel.

**Pařízkova (1977):**
- Männer: `%KF = 11.7 × log₁₀(Σ) − 11.6`
- Frauen: `%KF = 15.0 × log₁₀(Σ) − 12.6`

Diese Formel ist in deutschen sportwissenschaftlichen Studiengängen etabliert und liefert plausible Ergebnisse (Σ=139 mm → ~13–14 % bei Männern).

## Implementiert in
`artifacts/athletik/anthropometrie.py` → `koerperfett_jp11()`

## How to apply
Immer wenn jemand "JP11" oder "11-Hautfalten" erwähnt: Pařízkova-Logarithmus, nicht JP-Polynome.
