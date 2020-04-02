# Covid-19-Simulation - Point of View Deutschland (Stand 1.April 2020)

In Deutschland - wie in den meisten Ländern - stehen derzeit 3 Fragen im Vordergrund: 
* Reichen <b>kurzfristig</b>  die Krankenhaus- und Intensivkapazitäten für die zu erwartende Welle an Covid-19 Patienten aus?
* Wie kann ein <b>mittelfritiges</b> Szenario aussehen, um wieder zu einem geregelten Wirtschaftsleben zurück zu kehren?
* Welche Einschränkungen werden <b>langfristig</b> bestehen bleiben?

Aus Modellsicht spielen hier nicht nur die durchschnittlichen Reproduktionsraten in Abhängigkeit von der Zeit eine 
wesentliche Rolle,  sondern vor allem die individuellen Kontaktraten besonders gefährdeter Gruppen. 

## Kurzfristige Kapazitäten im Gesundheitssystem 
Wesentlich für die Abschätzung der kurzfristig zu erwartenden Maximalbelastung ist eine Einschätzung der effektiven
effektiven Reproduktionsrate vor dem dem von der Bundesregierung und den Ländern am 22.März.2020 beschlossenen Lockdown und 
aktuellen Wert. <br>

### Einschätzung der Reproduktionsrate R0 vor dem Lockdown

#### Datenlage in Deutschland
Eine exakte Messung der Reproduktionsrate ist unseres Erachtens nicht möglich. Hier spielen unterschiedliche Faktoren 
eine Rolle: 
* Sowohl für positive Tests, Einlieferungen auf Intensivstationen und Todesfälle gibt es Zeitverzüge zum 
Infektionszeitpunkt von einer bis zu drei oder sogar vier Wochen. Derzeitige Anstiege spiegeln also das 
Infektionsgeschehen vor Wochen wieder. 
* Die positiven Fälle hängen von den Testvorgaben (mit Symptomen und Kontakt) und den jeweiligen
    Testkapazitäten ab. Bei exponentiell steigenden Infektionen ist daher anzunehmen, dass die Dunkelziffer im Zeitverlauf steigt. 
* Aufgrund der immer noch sehr geringen Fallzahlen gibt es ein großes statistisches Rauschen und zufällige Ereignisse (Superspreading),
die sich in deutlich in der Fallzahlen ausgewirkt haben oder noch auswirken (im Nachlauf bei der Zahl der Todesfälle). 

<b>Als groben Bereich sehen wir eine Reproduktionsrate R0 vor dem Lockdown von 2.5 bis 3.5 in Deutschland als realistisch an. </b>

#### Vergleich mit anderen europäischen Ländern
Laut einer Studie aus dem Jahr 2006 (Quelle: https://journals.plos.org/plosmedicine/article/file?id=10.1371/journal.pmed.0050074&type=printable) 
sind die mittleren Kontaktraten in Europa sehr unterschiedlich: 
* Belgien:  11,84
* Deutschland:  7,95
* Finnland: 11,06
* Italien: 19,77
* Niederlande: 13,85
* UK: 11,74
Diese Werte scheinen eng korreliert mit den unterschiedlichen initialen Infektionsdynamiken in den verschiedenen Ländern
zu sein.<br>
Unsere Einschätzung ist daher: <b> Deutschland hat im Vergleich zu anderen europäischen Ländern ein deutlich geringere 
Reproduktionsrate unter uneingeschränkten Lebensbedingungen. </b>

#### Vergleich mit asiatischen Ländern
Für einen Vergleich der Kontaktraten unter Normalbedingungen liegen uns keine Studiendaten vor, die einen direkten Vergleich
ermöglichen. Qualitativ kann man aber sagen, dass auch unter Normmalbedigungen in einige asiatischen Ländern wie Japan oder
Südkorea das Halten von Abstand zum guten Ton gehört und das Tragen vom Masken in dichten Menschenmengen teilweise zum 
guten Ton gehört - nicht nur um sich selbst sondern auch um anderen zu schützen. <br>
Unser Einschätzung ist: <b>Sie Reproduktionsrate R0 in Deutschland ist höher als in Ländern wie Japan oder
Südkorea.</b>

### Einschätzung der Reproduktionsrate R nach dem Lockdown

#### Datenlage in Deutschland

Die aktuelle fallenden Zahlen von neuen Infektionen deuten darauf hin, dass die effektive Reproduktionsrate 
unter Lockdown-Bedingungen in Deutschland unter 1 gefallen ist. Aufgrund möglicher Verzerrungen (Limitierte Anzahl 
an Test, verstärkte Tests bei systemrelevanten Bevölkerungsteilen, ...) ist aber auch eine effektive Reproduktionsrate 
größer als 1 nicht komplett auszuschliessen. 

Wegen der kürzeren Inkubationszeit der Influenza müssen bei einem wirksamen Lockdown die gemeldeten Influenza-Infektionen früher zurückgehen als die Covid-19 Fälle. Laut Bericht des RKI zur KW 13 (21.-27.3.2020) ist dies der Fall (https://influenza.rki.de/Wochenberichte/2019_2020/2020-13.pdf). Die Zahl der gemeldeten Fälle ist in den letzten beiden Wochen stark gesunken: 19.130 (KW11), 10.712 (KW12), 3.528 (KW13). Wegen des saisonal bedingten Abklingens der Grippewelle kann daraus jedoch nur geschlossen werden, dass die Grippemeldungen einer deutlich Veringerung des allgemeinen Infektionsgeschehens nicht entgegenstehen. 

In Großbritanien wurde der Effekt des Lockdowns auf eine Reduktion der Kontakte um ca. 75% geschätzt 
(https://cmmid.github.io/topics/covid19/current-patterns-transmission/comix-impact-of-physical-distance-measures-on-transmission-in-the-UK.html)
Es ist zu beachten, dass sich relative Reduktionen nicht 1:1 übertragen lassen und die Kontaktraten unter 
Lockdown-Bedingungen sich in verschiedenen Länder vermutlich annähern. 

Grundsätzlich sehen wir, dass es bei der effektiven Reproduktionsrate deutliche Nachlaufeffekte geben kann. Auch nach 
Kontaktsperren laufen zunächst Folgeinfektionen in Familien weitesgehend ungehindert weiter. In Gemeinschaftsunterkünften
wie Pflegeheimen hängt der Nachlaufeffekt stark von den lokal getroffenen Schutzmaßnahmen ab. 

<b>Für Deutschland sehen wir daher drei Lockdown-Szenarien: 
* Best Case: Re=0.7
* Medium Case: Re=0.9
* Worst Case: Re=1.2
</b>

#### Lockdown Effekt in Italien
In Italien wurde der Lockdown am 9.3.2020 eingeführt. Tests auf Covid-19 werden in Italien erst bei mittleren bis schweren Symptomen oder sogar post mortem durchgeführt. Wegen begrenzter Testkapzitäten bei gleichzeitig hoher Dunkelziffer ist eine gleichbleibende Anzahl an gemeldeten Neuinfektionen noch kein eindeutiges Indiz dafür, dass der exponentielle Anstieg gestoppt wurde. <br> 
Auch die Anzahl der Intensivpatienten kann nicht verlässlich zur Einschätzung herangezogen werden, da in einigen Regionen die Kapazitätsgrenzen überschritten wurden und selbst bei sinkenden Zahlen im Bedarf weiterhin Zubau von Kapazitäten notwendig ist.<br>
Als erstes positiver Zeichen kann gesehen werden, dass die Zahl der Toten seit einigen Tagen sowohl in der am stärksten betroffenen Region Lombardei als auch in ganz Italien sinkt.

### Simulation kurzfristiger Szenarien
Die folgende Tabelle zeigt abhängig vom Szenario die benötigten ICU-Kapazitäten als Vielfaches der zum Lockdown belegten Kapazitäten. Lesebeispiel: Bei einer Belegung von 500 ICU-Betten zum Lockdowh-Zeitpunkt würden im Szenario R0=3,5 und Rlock=0,9 maximal 5950 Betten (11,9 x 500) 25 Tage nach dem Lockdown notwendig. 

| R0  | Rlock | Peak Tag | Peak/ICU Lock |
|-----|-------|----------|---------------|
| 2,5 | 0,7   | 20       | 4,7           |
| 2,5 | 0,9   | 25       | 7,2           |
| 2,5 | 1,2   | 112      | 29,5          |
| 3,5 | 0,7   | 20       | 9,0           |
| 3,5 | 0,9   | 25       | 11,9          |
| 3,5 | 1,2   | 99       | 33,8          |

R0 hat einen starken Einfluß auf die benötigte Bettenzahl, wenn Rlock kleiner als 1 ist. Hier kommt der Effekt zum Tragen, dass zum Lockdown-Zeitpunkt bereits deutlich mehr Infizierte vorhanden sind, die in den Folgewochen abgearbeitet werden müssen. 

Die Lockdown-Werte von 0,7 und 0,9 führen zwar immer noch zu einem kurzfristigen Anstieg des ICU Bedarfs um einen Faktor 4,7-11,9, führen vermutlich aber nicht zu einer Überlastung der Kapazitäten. 

Die beiden Szenarien mit Rlock=1.2 sagen eine sehr hohe Maximalbelastung nach erst 3-4 Monaten vorher. Hier bestünde die Herausforderung, die effektive Reproduktionszahl weiter zu senken und gleichzeitig die Produktivität wieder zu steigern. 

<b>Zusammenfassend kann sagen, dass Deutschland kurzfristig unter Lockdown-Bedingungen an einer Überlastung des Gesundheitssystems vorbei kommen könnte. Es kommen hier im Vergleich zu anderen europäischen Ländern mehrere positive Effekte zusammen: 
* Vergleichweise geringe Kontaktraten in Deutschland führen zu einer geringeren Basisreproduktionszahl. 
* Durch umfangreichere Tests konnte gerade in der Anfangsphase ein besseres Containment durchgeführt werden. Auch derzeit sind die Positivfälle in vielen Landkreisen noch so gering, dass eine frühzeitige Identifikation und Isolation von Kontaktpersonen möglich ist. 
* Deutschland hat im Vergleich zu anderen Ländern früher auf die Notbremse getreten. Bei einem Lockdown unter Re=1 kann bereits eine Woche längeres Warten einen Faktor 3 in der Maximalbelastung bedeuten (In der Lombardei waren zum Zeitpunkt des Lockdowns bereits 440 Covid-19 Patienten in Intensivbehandlung. Eine Woche zuvor waren es nur 127.).
* Die Intensivkapazitäten sind in Deutschland vergleichsweise hoch - jedoch verschafft auch eine 3-fache Kapazität bei einem ungebremsten Wachstum von z.B. 20% pro Tag nur einen zusätzlichen zeitlichen Puffer von ca. 6 Tagen.
</b>

Anmerkung: In Deutschland befindet sich ein Intensivregister zu Covid-19 Patienten im Aufbau (https://www.divi.de/register/kartenansicht). Da sich die Fallzahlen jedoch sowohl durch zusätzliche Patienten als auch durch neue hinzukommende Intensivstationen, die Covid-19-Fälle melden, erhöhen, ist die Zeitentwicklung nicht zuverlässlich einschätzbar. 

#### Detailergebnisse
Die Detailergebnisse mit den verwendeten Simualtionsparametern finden Sie [hier](https://github.com/PeterBorrmann1965/Covid-19-simulation/tree/master/szenarien/kurzfrist). 
![cfr](https://github.com/PeterBorrmann1965/Covid-19-simulation/blob/master/kurzfrist_cfr.svg)


