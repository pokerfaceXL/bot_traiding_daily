# Coordinator Research Protocol

## 1. Cel

Coordinator prowadzi systematyczne badania strategii tradingowych. Jego zadaniem nie jest wyszukiwanie jak największej liczby nowych strategii.

Jego zadaniem jest:

1. zrozumieć wyniki już przetestowanych strategii,
2. zidentyfikować mechanizm zysków i strat,
3. sformułować testowalną hipotezę,
4. przetestować najmniejszą zmianę mogącą odpowiedzieć na tę hipotezę,
5. zachować wyniki pozytywne i negatywne,
6. zdecydować, czy strategię rozwijać, zamrozić, odrzucić lub zastąpić innym mechanizmem.

Nowa strategia może zostać dodana tylko wtedy, gdy istnieje uzasadnienie wynikające z:
- obserwacji danych,
- analizy mechanizmu,
- wiarygodnego źródła zewnętrznego,
- nierozwiązanego problemu obecnej strategii,
- potrzeby dywersyfikacji mechanizmu.

Nie wolno rozpoczynać losowego wyszukiwania strategii.

---

## 2. Zasada nadrzędna

Każdy eksperyment musi zaczynać się od zdania:

> "Na podstawie wyniku X podejrzewam Y, dlatego testuję Z."

Przykład:

> Strategia DONCHIAN_55 jest zagregowanie dodatnia, ale przegrywa w określonych miesiącach. Podejrzewam, że straty są skupione w okresach fałszywych wybić podczas niskiej jakości trendu. Dlatego przetestuję filtr jakości wybicia, który nie opiera się wyłącznie na poziomie zmienności.

Niedozwolone:

> "Sprawdzę RSI, MACD, EMA, ATR i kilka innych filtrów, aby zobaczyć, co zadziała."

---

## 3. Pętla badawcza

Dla każdej aktywnej strategii wykonuj następującą pętlę:

1. Wybierz strategię bazową.
2. Przeczytaj wszystkie jej dotychczasowe wyniki i noty badawcze.
3. Zbuduj profil:
   - gdzie strategia zarabia,
   - gdzie traci,
   - jaka jest struktura wygranych,
   - jaka jest struktura strat,
   - które zmiany już odrzucono,
   - jakie ograniczenia pozostają nierozwiązane.
4. Wybierz jeden najważniejszy problem.
5. Zapisz hipotezę falsyfikowalną.
6. Zdefiniuj jedną oś eksperymentu.
7. Zdefiniuj metryki sukcesu przed uruchomieniem testu.
8. Uruchom test najpierw na danych rozwojowych.
9. Porównaj wynik z:
   - strategią bazową,
   - prostym benchmarkiem,
   - poprzednimi próbami tej samej rodziny.
10. Jeśli wynik jest obiecujący, uruchom niezależną walidację.
11. Zapisz wniosek, także jeśli wynik jest negatywny.
12. Zdecyduj o następnej iteracji na podstawie wyniku.

---

## 4. Priorytet rozwoju strategii

Priorytet nadaj strategiom według następującej kolejności:

### Poziom A — rozwijaj

Strategia:
- ma dodatni wynik netto po kosztach,
- ma wystarczającą liczbę transakcji,
- przeżywa limit ryzyka,
- działa na więcej niż jednym okresie lub symbolu,
- ma możliwy do wyjaśnienia mechanizm zysku,
- nie zależy od pojedynczej transakcji.

### Poziom B — analizuj warunkowo

Strategia:
- jest dodatnia tylko dla wybranych symboli lub interwałów,
- ma dodatni wynik zagregowany,
- ma nierówną regularność,
- wykazuje interesujący, ale niestabilny mechanizm,
- może być użyteczna jako składnik portfela.

Dla takich strategii nie należy natychmiast zmieniać parametrów. Najpierw zbadaj, kiedy działają, a kiedy nie działają.

### Poziom C — zamroź

Strategia:
- jest dodatnia, lecz ma za mało transakcji,
- wynik zależy od jednej serii,
- działa tylko w jednym krótkim okresie,
- ma niestabilny efekt między symbolami,
- nie przechodzi walidacji out-of-sample.

Zamrożenie oznacza zachowanie strategii i wyników, ale brak dalszego strojenia.

### Poziom D — odrzuć

Strategia:
- jest ujemna po kosztach,
- ma wysokie obsunięcie,
- nie przeżywa ograniczeń kapitałowych,
- pozostaje ujemna po rozsądnych zmianach,
- nie ma wiarygodnego mechanizmu przewagi.

Nie testuj ponownie odrzuconej strategii bez nowej informacji lub nowej hipotezy.

---

## 5. Jak analizować strategię, która ma mało sygnałów

Mała liczba sygnałów nie jest sama w sobie problemem.

Najpierw odpowiedz:

1. Czy mało sygnałów wynika z naturalnego mechanizmu strategii?
2. Czy sygnały mają dodatnią oczekiwaną wartość?
3. Czy pojedyncze wygrane są stabilne między okresami?
4. Czy strategia traci przez zbyt restrykcyjny filtr?
5. Czy zwiększenie liczby sygnałów pogarsza jakość wejść?
6. Czy strategia może być użyta jako wolniejszy składnik portfela?
7. Czy problemem jest częstotliwość sygnałów, czy brak przewagi?

Nie zwiększaj liczby transakcji tylko po to, aby wynik wyglądał bardziej regularnie.

Testuj kolejno:

1. bazową strategię bez dodatkowego filtra,
2. minimalne rozluźnienie istniejącego warunku,
3. zmianę interwału,
4. zmianę symbolu,
5. zmianę warunku wyjścia,
6. dopiero później nowy mechanizm wejścia.

Jeśli strategia ma mało sygnałów, ale wysoką jakość, należy rozważyć:
- wykorzystanie jej jako składnika portfela,
- większą wagę tylko po walidacji,
- połączenie z inną, nisko skorelowaną strategią.

Nie wolno sztucznie zwiększać liczby transakcji kosztem oczekiwanej wartości.

---

## 6. Jak analizować przegrane miesiące

Dla każdej strategii dodatniej agregowanie nie jest wystarczające.

Należy utworzyć tabelę miesięczną zawierającą:

- PnL netto,
- PnL brutto,
- liczbę transakcji,
- win rate,
- średnią wygraną,
- średnią stratę,
- maksymalne obsunięcie,
- udział kosztów,
- udział transakcji zakończonych initial stopem,
- udział transakcji zakończonych odwróceniem sygnału,
- medianę czasu trwania,
- warunki rynkowe.

Dla każdego stratnego miesiąca odpowiedz:

1. Czy wystąpiło zbyt dużo fałszywych wybić?
2. Czy straty wynikały z trendu bocznego?
3. Czy nastąpiła zmiana zmienności?
4. Czy strategia traciła na jednym symbolu, czy na całym koszyku?
5. Czy straty były małe i częste, czy duże i skupione?
6. Czy w tym miesiącu wystąpiły także sygnały, które później byłyby dużymi wygranymi?
7. Czy proponowany filtr usunąłby również zwycięskie transakcje?
8. Czy problem dotyczy wejścia, wyjścia, sizingu czy alokacji?

Nie wolno optymalizować bezpośrednio pod konkretne miesiące. Miesiące służą do odkrywania hipotez, a nie do ręcznego dopasowywania parametrów.

---

## 7. Reguła rozwijania zamiast porzucania

Jeśli strategia jest:
- dodatnia agregowanie,
- odporna na koszty,
- przeżywa limit obsunięcia,
- ma co najmniej jedną wiarygodną serię,
- ale ma nierówny miesięczny wynik,

to najpierw wykonaj diagnozę tej strategii.

Nie wolno od razu:
- przeszukiwać całego katalogu,
- dodawać losowych wskaźników,
- zmieniać wielu parametrów jednocześnie,
- wybierać tylko najlepszego symbolu,
- zwiększać częstotliwości transakcji,
- odrzucać strategii wyłącznie dlatego, że ma stratne miesiące.

W pierwszej kolejności zbadaj:
1. klasyfikację przegranych transakcji,
2. reżim rynkowy w momencie wejścia,
3. jakość wybicia,
4. opóźnienie sygnału,
5. warunek pozostawania w pozycji,
6. zależność wyniku od symbolu i interwału,
7. korelację z innymi strategiami.

---

## 8. Dozwolone typy eksperymentów

Eksperyment musi należeć do jednej kategorii:

### Entry refinement

Zmienia tylko jakość wejścia:
- potwierdzenie świecy,
- struktura wybicia,
- odległość od kanału,
- pozycja ceny względem zakresu,
- kierunek wyższego interwału,
- warunek dotyczący płynności.

### Exit refinement

Zmienia tylko zachowanie po wejściu:
- sposób opuszczenia pozycji,
- time stop,
- warunkowe wyjście dla słabego wybicia,
- częściowa realizacja,
- dynamiczne utrzymanie pozycji.

Nie używaj take-profit tylko po to, aby zwiększyć win rate. Jeśli usuwa duże wygrane, uznaj to za regresję mimo poprawy win rate.

### Regime filter

Filtr może być zaakceptowany tylko wtedy, gdy:
- poprawia wynik poza próbą,
- nie usuwa większości transakcji,
- nie opiera się na informacji dostępnej dopiero po wejściu,
- działa w więcej niż jednym okresie,
- jego działanie jest zrozumiałe.

### Position sizing

Sizing może być testowany dopiero po potwierdzeniu, że sam sygnał ma przewagę.

Nie używaj sizingu do maskowania ujemnej oczekiwanej wartości sygnału.

### Portfolio combination

Portfel testuj, gdy:
- składniki mają różne mechanizmy,
- ich straty nie są silnie skorelowane,
- wspólny kapitał i limit ryzyka są modelowane poprawnie,
- wynik nie zależy od jednej strategii.

---

## 9. Budżet eksperymentów

Każda hipoteza otrzymuje budżet.

Dla pojedynczej hipotezy:

- maksymalnie 1 główna zmiana mechanizmu,
- maksymalnie 1–3 parametry tej zmiany,
- najpierw mały sweep,
- później tylko najlepszy wariant,
- brak rozszerzania zakresu po zobaczeniu wyniku bez zapisania nowej hipotezy.

Jeżeli hipoteza nie poprawia wyniku po rozsądnym zakresie parametrów, oznacz ją jako:

```text
FALSIFIED
```

Nie zmieniaj zakresu tylko po to, aby znaleźć komórkę dodatnią.

---

## 10. Metryki i bramki

Nie wybieraj strategii według jednej metryki.

Każdy kandydat musi być oceniony według:

- net PnL po kosztach,
- PnL per trade,
- liczby transakcji,
- udziału dodatnich miesięcy,
- liczby stratnych miesięcy,
- maksymalnego obsunięcia,
- stabilności między symbolami,
- stabilności między interwałami,
- stabilności między okresami,
- koncentracji wyniku w pojedynczych transakcjach,
- kosztów jako procentu brutto,
- wyniku out-of-sample.

Win rate nie jest kryterium nadrzędnym.

Strategia z niższym win rate może być lepsza, jeśli zachowuje duże wygrane i ma dodatnią oczekiwaną wartość.

---

## 11. Walidacja

Podział danych musi być ustalony przed eksperymentem:

- development/train — do formułowania i testowania hipotez,
- validation — do wyboru finalistów,
- holdout — używany dopiero po zamrożeniu strategii.

Po wielu próbach najlepszy wynik na train nie jest wystarczającym dowodem. Należy uwzględniać liczbę przetestowanych wariantów i ryzyko selekcji najlepszego przypadku.

Finalista musi przejść:
1. walidację chronologiczną,
2. walk-forward lub podobną walidację,
3. test kosztów i poślizgu,
4. test na wielu symbolach,
5. test na wielu interwałach, jeśli strategia ma być wielointerwałowa,
6. test stabilności parametrów,
7. analizę koncentracji zysku,
8. test portfelowy,
9. niezależny holdout.

Nie promuj strategii do live wyłącznie na podstawie najlepszego wyniku train.

---

## 12. Internet i źródła zewnętrzne

Internet służy do:
- znalezienia mechanizmu lub hipotezy,
- poznania alternatywnych metod testowania,
- znalezienia znanych problemów danego typu strategii,
- porównania sposobów walidacji,
- znalezienia potencjalnego źródła dywersyfikującego.

Internet nie służy do:
- kopiowania przypadkowych strategii,
- uzasadniania testu samym faktem, że ktoś opublikował wskaźnik,
- wybierania strategii według popularności,
- zastępowania testu danych własnego systemu.

Każda informacja z internetu musi zostać przekształcona w hipotezę lokalną:

```text
Źródło:
Twierdzenie:
Mechanizm:
Hipoteza:
Sposób testu:
Kryterium falsyfikacji:
```

Źródła społecznościowe, Discord, X i YouTube traktuj jako generator hipotez, nigdy jako dowód przewagi.

---

## 13. Kiedy wolno rozpocząć nową rodzinę strategii

Nową rodzinę można rozpocząć tylko wtedy, gdy zachodzi jeden z warunków:

1. obecna rodzina została przebadana na głównych osiach i jej porażka ma wspólny mechanizm,
2. obecna strategia nie ma dodatniej oczekiwanej wartości,
3. dalsze modyfikacje tylko zmniejszają liczbę transakcji lub obcinają wygrane,
4. potrzebny jest mechanizm o niskiej korelacji,
5. dane ujawniają zjawisko, którego obecna rodzina nie potrafi wykorzystać.

Przed rozpoczęciem nowej rodziny zapisz:

```text
Why existing family is insufficient:
What mechanism is missing:
Why this family is different:
What evidence would reject it:
What is the maximum initial research budget:
```

---

## 14. Rejestr decyzji

Po każdym eksperymencie zapisz:

```yaml
experiment_id:
date:
base_strategy:
hypothesis:
motivation:
change_tested:
parameters:
data_split:
baseline:
metrics_before:
metrics_after:
oos_result:
cost_model:
number_of_trials:
result:
decision:
reason:
next_action:
```

Pole `decision` musi przyjąć jedną z wartości:

```text
CONTINUE
REFINE
CONDITIONAL
FREEZE
FALSIFIED
PROMOTE_TO_VALIDATION
REJECT
```

---

## 15. Obowiązkowy raport Coordinatora

Na koniec każdej serii badań Coordinator musi odpowiedzieć:

1. Która strategia jest obecnie najlepsza?
2. Dlaczego jest najlepsza?
3. Czy przewaga pochodzi z wielu transakcji, czy kilku dużych wygranych?
4. W jakich warunkach zarabia?
5. W jakich warunkach traci?
6. Które hipotezy zostały odrzucone?
7. Jaki problem pozostaje nierozwiązany?
8. Jaki jest następny eksperyment i dlaczego?
9. Dlaczego nie testuje teraz kolejnych losowych strategii?
10. Jaki wynik potwierdziłby lub obalił następną hipotezę?

Jeśli Coordinator nie potrafi odpowiedzieć na pytania 4–9, nie może rozpocząć szerokiego searchu.

---

## 16. Podział pracy na workerów (delegacja powtarzalnego potoku po-testowego)

Coordinator jest modelem wysokiego poziomu i jego tokeny są drogie. Dlatego **nie wykonuje
ręcznie powtarzalnej pracy po-testowej** — rozdrabnia ją na małe, niezależne tickety i zleca je
workerom na możliwie **najniższym modelu/poziomie myślenia**, który poprawnie wykona zadanie.

### 16.1 Podział ról

- **Coordinator (model wysoki, thinking high)** robi wyłącznie pracę wymagającą osądu:
  autopsja, projekt hipotezy (§2/§8), wartość pola `decision` (§14), raport §15, ocena czy
  falsyfikatory zostały spełnione, wybór następnego kroku.
- **Worker (model niski / codex, thinking low–medium)** robi pracę mechaniczną i
  deterministyczną: uruchomienie backtestu wg zamrożonej specyfikacji, liczenie metryk, budowa
  tabel, wypełnianie szkieletu rejestru, aktualizacja profilu z policzonych liczb, regeneracja
  digestu.

### 16.2 Reguły zlecania

- Maksymalnie **2 workery naraz**. Przed spawnem sprawdź `limen jobs --running`.
- **Ekonomia modelu:** zadania wg precyzyjnej specyfikacji idą na provider **codex**
  (`--provider openai-codex`): `gpt-5.3-codex-spark` dla rutyny (czysta pandas/formatowanie),
  `gpt-5.6-sol` dla zadań wrażliwych na przyczynowość lub kod silnika. Silnik Claude rezerwuj
  do review i trudnego rozumowania. Dobieraj **najniższy poziom, który poprawnie wykona
  zadanie.**
- Ticket to wskaźnik, nie prompt — instrukcja spawn jest krótka, pełna specyfikacja leży w
  pliku ticketu.

### 16.3 Standardowy potok po-testowy (po każdym eksperymencie)

Gdy worker T0 wyprodukuje surowe wyniki (`output/f006_<exp>/{results,monthly,trades}.csv`),
Coordinator **nie liczy metryk sam** — kopiuje gotowe szablony z `spec/features/_post_test/`,
podstawia placeholdery i spawn-uje workery (szczegóły i komendy: `spec/features/_post_test/DISPATCH.md`).

| ticket | co robi | §protokołu | model |
| --- | --- | --- | --- |
| T0-run | implementuje + uruchamia eksperyment wg zamrożonej pre-rejestracji | §8/§9/§11 | codex sol |
| T1-metrics | net po kosztach, PnL/trade, n_trades, % dod. mies., stratne mies., maxDD, koszt%brutto, koncentracja top-N, stabilność symbol/interwał/okres | §10 | codex spark |
| T2-monthly | tabela miesięczna + klasyfikacja stratnych miesięcy (opisowo z danych, pyt. §6.1–8) | §6 | codex spark |
| T3-registry | szkielet rejestru §14 wypełniony z T1/T2; `decision/reason/next_action` zostają puste dla Coordinatora | §14 | codex spark |
| T4-profile | aktualizacja wierszy profilu (Core metrics, Stability, Tested modifications) z T1/T2; status zostaje dla Coordinatora | §4 | codex spark |
| T5-digest | regeneracja cross-family digest + kontrola sanity | — | codex spark |

T1–T5 są wzajemnie niezależne poza kolejnością danych (T3/T4 czytają wynik T1/T2), więc przy
limicie 2 workerów puszczaj je parami (np. T1+T2, potem T3+T4, potem T5).

### 16.4 Czego NIGDY nie delegować

Wartość pola `decision` (§14), raport §15, projekt następnej hipotezy, ocena czy wynik
spełnia/obala kryterium falsyfikacji. To jest nieredukowalna praca Coordinatora.

### 16.5 Brak ponownego wyprowadzania

Szablony ticketów i gotowe komendy spawn żyją w `spec/features/_post_test/`. Coordinator **nie
projektuje tych ticketów od nowa** — kopiuje szablon do `spec/features/active/<exp>-<Tn>/`,
podstawia `{{EXPERIMENT_ID}} / {{OUTPUT_DIR}} / {{PROFILE}} / {{BASELINE}}` i spawn-uje. To jest
proces powtarzalny; jedyną zmienną jest nazwa eksperymentu.