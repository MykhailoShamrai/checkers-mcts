# ROADMAPA PROJEKT 2 (MCTS/UCT + warcaby)

## 1. Cel roadmapy
Ten plan przekłada wymagania przedmiotu na konkretne kroki implementacyjne i badawcze.
Priorytetem jest czesc badawcza (hipotezy, eksperymenty, raport), a kod ma byc narzedziem do wiarygodnego sprawdzenia hipotez.

## 2. Stan obecny repo (na dzis)
- Jest zalazek silnika gry: reprezentacja planszy, ruchu i stanu gry.
- Krytyczny moduł zasad gry (`rules.py`) jest jeszcze niezaimplementowany.
- Brak testow silnika (poza szkieletem katalogu `tests/`).
- Brak graczy AI (UCT, warianty, alpha-beta).
- Brak GUI do gry czlowiek-komputer.
- Brak harnessu eksperymentalnego i analizy wynikow.

Wniosek: trzeba przejsc pelny cykl od silnika i testow, przez AI i GUI, do eksperymentow, analizy i raportu.

## 3. Zakres obowiazkowy wynikajacy z wymagan
1. UCT bazowy (bez modyfikacji).
2. Dwa usprawnienia UCT (min. jedno z literatury).
3. Heurystyczny gracz dedykowany grze.
4. Wlasna hipoteza badawcza inna niz powyzsze porownania.
5. Interfejs czlowiek-komputer i testy na min. 5 osobach.
6. Powtarzalnosc eksperymentow (ziarna RNG i wielokrotne uruchomienia).
7. Raport z wizualnym, czytelnym przedstawieniem wynikow.

## 4. Szczegolowa roadmapa (krok po kroku)

## Krok 0 - Zamrozenie specyfikacji badania
Status: DONE (2026-06-13)
Artefakty:
- `STEP0_SPECYFIKACJA_BADANIA.md`
- `STEP0_MACIERZ_EKSPERYMENTOW.csv`

### Co trzeba zrobic
- Potwierdzic finalny wariant zasad (z CLAUDE.md) i niczego nie zmieniac bez dopisania uzasadnienia.
- Spisac finalna liste hipotez i metryk.
- Ustalic minimalny zestaw eksperymentow, ktory na pewno musi wejsc do raportu.

### Wynik (artefakty)
- Jedna lista hipotez (H1..H4) i metryk (win rate, dlugosc gry, czas/ruch, odchylenie).
- Jedna tabela planu eksperymentow (jakie algorytmy i parametry).

### Kryterium ukonczenia
- Kazdy członek zespolu umie jednym zdaniem powiedziec: co porownujemy, jak i po co.

## Krok 1 - Silnik zasad gry (najwyzszy priorytet)
Status: DONE (implementacja, 2026-06-13)
Uwagi:
- Pelna walidacja kroku przez testy jednostkowe i scenariuszowe w Kroku 2.

### Co trzeba zrobic
- Zaimplementowac w `checkers/engine/rules.py`:
  - legalne ruchy bez bicia,
  - bicia pionkow i damek,
  - wymuszenie bicia,
  - wielobicia,
  - zasady dla damek latajacych,
  - promocje do damki,
  - `apply_move` bez mutacji planszy wejsciowej.
- Jawnie zdecydowac i opisac zachowanie przy promocji w trakcie sekwencji bicia.

### Wynik (artefakty)
- Dzialajacy generator ruchow + wykonywanie ruchu.
- Udokumentowana decyzja o promocji mid-sequence.

### Kryterium ukonczenia
- Silnik zwraca tylko legalne ruchy i nie narusza zasad wariantu gry.

## Krok 2 - Testy silnika (warunek konieczny przed AI)
### Co trzeba zrobic
- Dodac testy jednostkowe i scenariuszowe w `tests/`:
  - ustawienie poczatkowe,
  - wymuszenie bicia,
  - wielobicia pionkow,
  - bicia i wielobicia damek,
  - promocje,
  - brak mutacji wejscia w `apply_move`,
  - terminale: wygrana przez brak ruchu, remis przez limit ruchow.
- Dodac 2-3 testy regresyjne pod bledy znalezione podczas implementacji.

### Wynik (artefakty)
- Stabilny pakiet testow uruchamiany jednym poleceniem `pytest`.

### Kryterium ukonczenia
- Wszystkie testy przechodza lokalnie i po wielokrotnym uruchomieniu.

## Krok 3 - Bazowy UCT
Status: DONE (2026-06-13)

### Co trzeba zrobic
- Zaimplementowac gracza `players/mcts/uct.py`:
  - selection (UCB1),
  - expansion,
  - simulation (losowa),
  - backpropagation.
- Dodac parametry: `iterations`, `c`, `seed`.
- Zapewnic deterministycznosc dla tego samego ziarna.

### Wynik (artefakty)
- Dzialajacy gracz UCT uruchamialny w grze i w turniejach automatycznych.

### Kryterium ukonczenia
- Dla stalego seed wynik wyboru ruchu jest powtarzalny.

## Krok 4 - Usprawnienie UCT nr 1 (z literatury)
Status: DONE (2026-06-13) — UCT + minimax hybrid (Baier & Winands 2014)

### Co trzeba zrobic
- Zaimplementowac `uct_minimax.py` (hybryda UCT + plytkie minimax) LUB
- `uct_early_term.py` (wczesne obcinanie symulacji + heurystyka materialu, opcjonalnie blending alpha).
- Parametryzowac glebokosc/limit symulacji i seed.

### Wynik (artefakty)
- Pierwszy wariant ulepszonego UCT zrodlowo oparty o publikacje.

### Kryterium ukonczenia
- Wariant uruchamia sie stabilnie i ma komplet parametrow do strojenia.

## Krok 5 - Usprawnienie UCT nr 2 (drugi wariant)
Status: DONE (2026-06-13) — UCT + early termination (Lorentz 2016, Lanctot 2014)

### Co trzeba zrobic
- Zaimplementowac drugi wariant (ten, ktory nie zostal wybrany w Kroku 4) albo inne sensowne usprawnienie opisane w literaturze.
- Ujednolicic interfejs uruchamiania obu wariantow.

### Wynik (artefakty)
- Dwa niezalezne warianty usprawnionego UCT gotowe do porownania.

### Kryterium ukonczenia
- Oba warianty da sie uruchomic tym samym harnesssem eksperymentalnym.

## Krok 6 - Gracz heurystyczny (benchmark specjalizowany)
Status: DONE (2026-06-13)

### Co trzeba zrobic
- Zaimplementowac `players/heuristics.py` (ocena pozycji) oraz `players/alphabeta.py`.
- Dodac iterative deepening, alfa-beta i limit czasu/glebokosci.
- Dobrac cechy heurystyki (material, mobilnosc, centrum, bliskosc promocji).

### Wynik (artefakty)
- Dzialajacy benchmark heurystyczny do porownan z UCT.

### Kryterium ukonczenia
- Gracz stabilnie podejmuje ruchy i nie lamie zasad.

## Krok 7 - GUI i testy czlowiek-komputer (min. 5 osob)
Status: DONE (implementacja GUI, 2026-06-13)
Uwagi: Testy na 5 osobach do przeprowadzenia reczne.

### Co trzeba zrobic
- Zbudowac GUI (plansza, klikniecia, podswietlenia legalnych ruchow, koniec gry).
- Dodac konfiguracje: human vs bot, bot vs bot, wybor algorytmu i parametrow.
- Przygotowac prosty formularz ewaluacyjny dla 5 osob:
  - czytelność interfejsu,
  - odczuwalna sila bota,
  - bledy/niejasnosci zasad,
  - subiektywna satysfakcja.

### Wynik (artefakty)
- Interfejs gry i protokoly z co najmniej 5 testow uzytkownikow.

### Kryterium ukonczenia
- Co najmniej 5 osob rozegralo partie i macie zapisane obserwacje.

## Krok 8 - Harness eksperymentalny i dane
Status: DONE (2026-06-13)

### Co trzeba zrobic
- Zaimplementowac `experiments/tournament.py` i `experiments/run_experiment.py`:
  - seria N gier,
  - zmiana kolorow,
  - lista seedow,
  - logowanie metryk do CSV.
- Minimalny plan eksperymentow:
  - UCT bazowy vs heuristic,
  - UCT wariant 1 vs heuristic,
  - UCT wariant 2 vs heuristic,
  - sweep po `c` i budzecie iteracji.

### Wynik (artefakty)
- Powtarzalny pipeline, ktory generuje surowe CSV do analizy.

### Kryterium ukonczenia
- Ten sam seed reprodukuje ten sam przebieg/rezultat; inne seedy daja rozklad wynikow.

## Krok 9 - Analiza statystyczna i wizualizacje
Status: DONE (2026-06-13)

### Co trzeba zrobic
- Zaimplementowac `experiments/analysis.py`:
  - agregacje srednia/odchylenie,
  - przedzialy ufnosci lub error bars,
  - wykresy porownawcze.
- Zidentyfikowac konfiguracje najlepiej i najgorzej dzialajace.

### Wynik (artefakty)
- Wykresy i tabele zagregowane gotowe do raportu.

### Kryterium ukonczenia
- Da sie odpowiedziec na kazda hipoteze na podstawie danych, nie intuicji.

## Krok 10 - Raport koncowy + prezentacja
Status: IN PROGRESS (szablon LaTeX gotowy, 2026-06-13)
Uwagi: Raport wymaga uzupelnienia wynikami po pelnym runie eksperymentow + testach na 5 osobach.

### Co trzeba zrobic
- Napisac raport tak, by bez kodu dalo sie zrozumiec co, jak i dlaczego zbadano.
- Dodac:
  - streszczenie ~250 slow,
  - opis wykorzystania LLM (kod + raport),
  - bibliografie recenzowanych publikacji,
  - wnioski odnoszace sie 1:1 do hipotez.
- Przygotowac prezentacje 10 min (problem, metoda, najciekawsze wyniki, wnioski).

### Wynik (artefakty)
- Pelny raport, slajdy, link do repo/zip.

### Kryterium ukonczenia
- Kazda czesc oceny ma pokrycie: konspekt, raport, prezentacja, kod.

## 5. Proponowane hipotezy (wersja robocza)
- H1: UCT z odpowiednio dobranym `c` osiaga wyzszy win rate niz baseline heurystyczny przy malym i srednim budzecie iteracji.
- H2: UCT + minimax (plytkie rollouty) daje stabilniejsza jakosc decyzji niz czysty UCT (mniejsza wariancja wynikow miedzy seedami).
- H3: UCT + early termination + heurystyka skraca czas/ruch przy porownywalnym win rate do bazowego UCT.
- H4 (wlasna, inna): Obnizenie limitu ruchow (np. 150 -> 100) zmienia ranking algorytmow i faworyzuje metody bardziej agresywne materialowo.

## 6. Minimalna macierz eksperymentow
- Gracze: `uct`, `uct_minimax`, `uct_early_term`, `alphabeta`.
- Seedy: min. 20-30 roznych seedow na konfiguracje.
- Partie na punkt: min. 50 (z zamiana kolorow).
- Budzety UCT: 100, 500, 1000, 5000, 10000 iteracji.
- Stala UCB `c`: np. 0.1, 0.3, 0.7, 1.0, 1.4, 2.0, 3.0.

## 7. Kolejnosc realizacji (praktyczna)
1. Krok 1 + Krok 2 (silnik i testy) - bez tego dalej nie ma sensu.
2. Krok 3 (bazowy UCT).
3. Krok 6 (heurystyczny benchmark), zeby miec do czego porownywac.
4. Krok 4 i Krok 5 (dwa warianty UCT).
5. Krok 8 + Krok 9 (eksperymenty i analiza).
6. Krok 7 rownolegle (GUI i testy na 5 osobach).
7. Krok 10 na koniec (raport + prezentacja).

## 8. Definition of Done calego projektu
- Wszystkie 4 typy graczy sa zaimplementowane i porownane.
- Jest co najmniej 1 wlasna hipoteza niezalezna od prostego porownania graczy.
- Eksperymenty sa wielokrotnie powtorzone na wielu seedach i reprodukowalne.
- Jest interfejs human-computer i testy na min. 5 osobach.
- Raport i prezentacja opieraja sie na danych z eksperymentow, a nie opisie implementacji.
