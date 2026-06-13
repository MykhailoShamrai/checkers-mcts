# KROK 0 - ZAMROZENIE SPECYFIKACJI BADANIA

Status: DONE
Data zamrozenia: 2026-06-13

## 1. Finalny wariant zasad (zafiksowany)
Projekt realizuje wariant warcabow opisany w CLAUDE.md.

Reguly gry obowiazujace w eksperymentach:
- Plansza 8x8, ruch tylko po ciemnych polach.
- 12 pionkow na strone, WHITE zaczyna.
- Pion porusza sie o jedno pole po przekatnej do przodu.
- Pion bije do przodu i do tylu.
- Bicie jest obowiazkowe.
- Wielobicia sa obowiazkowe i kontynuowane tym samym pionem/damka az do konca sekwencji.
- Damki sa latajace: ruch i bicie po calej przekatnej, ladowanie na dowolnym pustym polu za bitym pionem.
- Figura bita nie moze byc zbita ponownie w tej samej sekwencji.
- Promocja piona do damki na ostatnim rzedzie.
- Limit ruchow: 150 plys, po przekroczeniu remis.
- Zasada maksymalnego bicia: wylaczona domyslnie (dopuszczalne dowolne pelne sekwencje bicia).

Decyzja implementacyjna o promocji podczas wielobicia:
- Pion promuje sie po zakonczeniu calego ruchu (na finalnym polu), nie w trakcie.
- Jesli pion dotrze do rzedu promocji w trakcie sekwencji, kontynuuje sekwencje jako pion.

Uwaga o zmianach zasad:
- Kazda zmiana zasad po dacie zamrozenia wymaga dopisku w raporcie:
  - co zmieniono,
  - dlaczego,
  - jaki byl wplyw na eksperymenty.

## 2. Hipotezy badawcze (finalne)
H1 (bazowa):
- Czysty UCT, po strojeniu parametru C, osiaga wyzszy win rate od gracza heurystycznego dla niskiego i sredniego budzetu iteracji.

H2 (literaturowa):
- UCT + minimax rollout (plytki) obniza wariancje wynikow miedzy seedami wzgledem czystego UCT.

H3 (literaturowa):
- UCT + early termination + ewaluacja heurystyczna skraca sredni czas na ruch przy porownywalnym win rate do czystego UCT.

H4 (wlasna, inna niz porownanie samych graczy):
- Zmiana limitu ruchow z 150 na 100 zmienia ranking algorytmow i zwieksza odsetek zwyciestw graczy agresywnie materialowych.

## 3. Metryki i sposob liczenia
Metryki glówne:
- Win rate: odsetek wygranych na kolor i lacznie.
- Draw rate: odsetek remisow.
- Avg game length: srednia liczba plys na partie.
- Avg time per move: sredni czas decyzji na ruch.
- Variance across seeds: odchylenie standardowe win rate i czasu/ruch.

Metryki pomocnicze:
- Rozklad rezultatow dla kolorow (bias pierwszego ruchu).
- Liczba partii zakonczonych limitem ruchow.

Zasady raportowania:
- Dla kazdej konfiguracji podawac srednia, odchylenie standardowe oraz 95% CI (jezeli mozliwe).
- Wyniki pokazywac lacznie i z podzialem na kolor.

## 4. Minimalny zestaw eksperymentow (must have)
Zestaw graczy:
- UCT (bazowy).
- UCT + minimax.
- UCT + early termination.
- Alpha-beta heurystyczny (benchmark).

Serie obowiazkowe:
- UCT vs AlphaBeta.
- UCT_Minimax vs AlphaBeta.
- UCT_EarlyTerm vs AlphaBeta.
- UCT vs UCT_Minimax.
- UCT vs UCT_EarlyTerm.

Powtarzalnosc:
- Dla kazdej konfiguracji: min. 50 partii.
- Min. 20 roznych seedow.
- Zmiana kolorow miedzy algorytmami (balans).
- Logowanie seedu dla kazdej partii.

Parametry sweep:
- C: 0.1, 0.3, 0.7, 1.0, 1.4, 2.0, 3.0
- Iteracje: 100, 500, 1000, 5000, 10000

Eksperyment dla H4:
- Powtorzyc wybrane porownania dla move_limit=100 i move_limit=150.

## 5. Ryzyka i kontrola jakosci
Ryzyka:
- Blad implementacji zasad gry wypacza wszystkie wyniki.
- Nieustabilizowana losowosc (brak seedow) uniewaznia porownania.
- Za maly budzet partii daje niestabilne wnioski.

Kontrola:
- Najpierw testy silnika i walidacja legalnosci ruchow.
- Seed przekazywany jawnie i logowany do CSV.
- Kontrola biasu koloru przez zamiane stron.

## 6. Kryterium zaliczenia Kroku 0
Krok 0 uznajemy za zamkniety, gdy:
- zasady sa zamrozone,
- hipotezy i metryki sa finalne,
- macierz eksperymentow jest gotowa,
- zespol nie zmienia zalozen bez dopisku uzasadnienia.
