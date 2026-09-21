# Vision

Mamy istniejącego, działającego na żywo bota do handlu kryptowalutami (Bybit USDT perpetual, long/short) i chcemy poprawić jego rentowność. Celem projektu jest znalezienie i zweryfikowane potwierdzenie strategii (lub małego portfela strategii), która generuje dodatni wynik netto niemal każdego dnia miesiąca — w ramach uzgodnionego kapitału, stawki i limitu obsunięcia — zamiast opierać się na pojedynczych dużych transakcjach. Coordinator ma samodzielnie prowadzić to badanie: od zbudowania wiarygodnej symulacji, przez systematyczne testowanie hipotez (istniejący katalog strategii, Lorentzian Classification i własne pomysły), aż po niezależną walidację — zanim jakikolwiek kandydat trafi na produkcję. Obecna produkcja pozostaje nietknięta przez cały czas badań.

## Product principles

- Rozwijamy istniejącego bota Python do handlu kryptowalutami na Bybit USDT perpetual, long i short.
- Celem jest dodatni wynik netto portfela każdego dnia miesiąca (100% dni dodatnich), przy maksymalizacji zysku w ramach ustalonego ryzyka i interwałach 5 min–4 h. To kierunek optymalizacji do empirycznego zbadania, nie gwarancja przyszłego wyniku.
- Uzgodnione ograniczenia: stała stawka bazowa 100 USD na wejście oraz maksymalne obsunięcie całego kapitału 50%. Zgodnie z obecnym kodem stawka jest przed dźwignią (nominał = 100 × leverage), bez automatycznej kapitalizacji; kapitał początkowy całego portfela wynosi 500 USD (initial_equity = 500), wspólnie dla wszystkich strategii i symboli.
- Dopuszczalne odchylenie od celu określa procent dni bez zysku w każdym pełnym miesiącu; obejmuje dni stratne i zerowe. Uzgodniona tolerancja wynosi 20% (minimum 80% dni dodatnich); dokładna metodyka jest zapisana w build.md. Regularność zysku nie usprawiedliwia ujemnego wyniku netto ani przekroczenia limitu obsunięcia.
- Strategia ma dostosowywać decyzje do obserwowanego zachowania rynku: kierunku, zmienności, płynności i zmian warunków. Nie zakładamy, że rynek musi zapewniać codzienną okazję ani odpowiadać wybranej z góry strategii. Brak pozycji jest pełnoprawną decyzją, gdy nie ma potwierdzonej przewagi po kosztach — ochrona kapitału i poprawność decyzji mają pierwszeństwo przed wymuszaniem dodatniego dnia; dni bez zysku nadal uczciwie wliczamy do tolerancji 20%.
- Przewaga strategii musi utrzymać się poza okresem doboru parametrów, po kosztach, przy realistycznej realizacji zleceń i na danych dostępnych w chwili decyzji.
- Nie zakładamy z góry, że istnieje jedna najlepsza strategia dla całego crypto. Badamy proste hipotezy trendu, wybicia i powrotu do średniej; filtry reżimu i portfel dodajemy, gdy uzasadniają je wyniki.
- Każdy wynik musi być odtwarzalny z wersji kodu, konfiguracji, danych i rejestru eksperymentu. Zachowujemy również wyniki nieudane.
- Coordinator samodzielnie wyciąga wnioski z danych, formułuje sprawdzalne hipotezy, bada źródła internetowe i implementuje własne rozwiązania w środowisku badawczym. Katalog strategii jest punktem startowym, a każda nowa metoda wymaga porównania z prostszym wariantem i walidacji poza danymi doboru.
- Coordinator ma wykonać uzgodniony budżet badań i pokazać najlepsze zmierzone przybliżenie celu, odstęp od tolerancji oraz kompromis między regularnością, zyskiem i ryzykiem. Nie kończy zadania samym stwierdzeniem, że codzienny zysk jest nierealny; nie obiecuje też osiągnięcia celu ani nie ukrywa niepowodzeń. Brak dowodów blokuje promocję do live, nie rzetelny raport badawczy.
- Wyniki badań zapisujemy lokalnie na serwerze projektu, w formacie czytelnym dla AI i człowieka. Wysyłka backtestów do Apex jest zawieszona; Apex nie jest zależnością procesu badawczego.
- Właściciel zgłasza, że wykonanie live działa poprawnie. Traktujemy je jako istniejącą bazę; nie uznajemy tego za niezależnie potwierdzoną poprawność ani rentowność.

## Current direction

- Najpierw zweryfikować symulację, dopiero potem rozpocząć szerokie poszukiwanie strategii.
- Zacząć od istniejących strategii i interwałów 1 h / 4 h; 5 min / 15 min / 30 min uwzględnić w tej samej metodyce po uwzględnieniu kosztów. Wyjaśnić osobno politykę trzymania przez noc.
- Porównywać kandydatów z aktualnymi konfiguracjami bota na identycznych okresach, danych i zasadach kapitału; finalny wybór poprzedzić walidacją portfela na wydzielonym holdoucie.
- Coordinator aktywnie bada aktualne źródła internetowe, aby wybierać skuteczne metody wyszukiwania parametrów i przyspieszania badań. Optuna jest wymienna; decyzję wyznacza jakość wyniku w ustalonym budżecie czasu oraz poprawność symulacji, potwierdzone pomiarami.
- Uwzględnić Lorentzian Classification z advanced-ta jako kandydata badawczego. Odtworzyć wariant możliwie zbliżony do jej wcześniejszych testów i porównać go z obecnymi strategiami według tych samych kosztów, ryzyka i celu regularności.
- Zachować działającą produkcję podczas badań. Zmiany wspólnej logiki muszą mieć testy zgodności; wdrożenie na prawdziwe środki wymaga decyzji właściciela.
- Coordinator ma prowadzić małe zadania z mierzalnym rezultatem i dowodami wykonania, dobierając budżet reasoning effort do trudności zadania (patrz build.md, sekcja „Dobór modelu i reasoning effort"), żeby nie marnować budżetu na proste kroki.
