# Шортси з реакцій стрімерів для TikTok і YouTube Shorts

Формат: вертикальне відео 1080x1920. Зверху камера стрімера, знизу те, на що він дивиться,
на стику біла плашка з коротким заголовком англійською, нижче субтитри, де слово, яке зараз
звучить, підсвічується жовтим. Гучність вирівнюється до мінус 14 LUFS. Приклад зроблено зі
стріму IShowSpeed, де він дивиться трейлер GTA 6 (`jobs/speed_kfc.json`).

## Середовище

Сесію треба запускати в середовищі **read video**. Там на старті ставляться шрифти, sox,
faster-whisper, pysubs2 і решта, а також відкритий доступ до Hugging Face, звідки качається
модель розпізнавання. Модель large-v3-turbo докачується при першому запуску, це близько хвилини.
Chromium і Playwright для плашки є в базовому образі.

## Як зробити ролик

1. Джерело користувач кидає файлом у чат, воно лягає в `/root/.claude/uploads/...`.
   Найкраще горизонтальний запис стріму в 1080p. Джерело в 360p виходить м'яким.
2. Пошук моментів у довгому шматку:
   `python3 shorts/moments.py SOURCE.mp4 --out WORK` друкує найгучніші місця з мовою навколо
   і пише повну розшифровку в `WORK`. Година стріму розпізнається приблизно за 30 хвилин.
3. Рамки для камери і контенту: `python3 shorts/make_short.py --grid SOURCE.mp4 120 --grid-out WORK/grid.png`
   дає кадр із сіткою і підписами в пікселях джерела. За ним визначаються `top` і `bottom` як `[x, y, w, h]`.
   Варто глянути кілька кадрів по всьому моменту, щоб стрімер не виходив з рамки.
4. Job-файл за зразком `jobs/speed_kfc.json`. Усі поля описані в шапці `make_short.py`.
5. `python3 shorts/make_short.py job.json`. Тридцять секунд ролика збираються приблизно за хвилину.
6. Перевірити кілька кадрів результату. Неправильно розпізнані слова виправляються через `fixes`
   або прямо у файлі `OUT.words.json`, після чого збірку треба запустити ще раз.
7. Віддати файл користувачу і написати опис і хештеги, як нижче.

## Відео без камери стрімера: геймплей, трейлери, фанатські концепти

`make_edit.py` робить інший макет. Кадр обрізається по вертикалі до 1080x1240 і стоїть посередині,
зверху і знизу розмита копія, плашка лежить на верхньому краї кадру. Сегменти йдуть у заданому порядку,
кожному можна задати центр кадру `x`, плавну панораму `x_end`, зум, сповільнення `speed` і глухий удар
`boom` на секунді влучання, а `whoosh` дає шелест на склейці. Короткі написи на кшталт WAIT FOR IT
задаються в `texts`. Приклади: `jobs/concept_*.json`, зроблені з фанатського концепту GTA 6.

Порядок роботи той самий: подивитися кадри (контактні аркуші з рамкою 48 відсотків ширини показують,
що потрапить у вертикальний кадр), записати сегменти, зібрати, перевірити кадри.

Концепти й фанатські ролики підписуються як fan concept у плашці і в описі. Видавати їх за справжній
геймплей не варто: після релізу це одразу видно, і в коментарях, і в скаргах.

## Що враховано в оформленні

Плашка тримається в межах 900 px по ширині, субтитри за замовчуванням стоять на висоті
`split + 470`. Так текст не залазить під кнопки праворуч і під опис унизу, і в TikTok, і в Shorts.
Зум на камеру (`punch`) варто ставити на крики і головні фрази, по одному-два на кожні 10 секунд.
Курсор миші та іконки плеєра з джерела лишаються як є.

## Опис і хештеги

TikTok: один рядок про суть моменту з емодзі і 4 або 5 хештегів, ім'я стрімера, гра, тема.

YouTube Shorts: назва до 100 символів у стилі заголовка на плашці плюс 2 хештеги, опис у
одне-два речення, хештеги в кінці опису, теги в окреме поле. Закріплений коментар із питанням
до глядачів збирає відповіді.

Приклад для `speed_kfc`:

```
TikTok
Speed saw KFC in the GTA 6 trailer and lost it 😭🍗 #ishowspeed #speed #gta6 #gta6trailer #gtavi

YouTube Shorts
Title: Speed found KFC in GTA 6 😭🍗 #ishowspeed #gta6
Description: IShowSpeed spots KFC in the GTA 6 trailer, then decides one of the characters is Keanu Reeves 😭
#ishowspeed #gta6 #gta6trailer #speed #shorts
Tags: ishowspeed, speed, gta 6, gta vi, gta 6 trailer, ishowspeed gta 6, speed reacts, gta 6 reaction, kfc, keanu reeves
Pinned comment: Would you play GTA 6 just to eat at KFC? 🍗
```

Приклад для фанатського концепту (`concept_montage`):

```
TikTok
Fans couldn't wait for GTA 6 so they made their own 😭 #gta6 #gtavi #gta6concept #gaming #rockstargames

YouTube Shorts
Title: Fans couldn't wait for GTA 6 so they made their own 😭 #gta6 #shorts
Description: Fan made GTA 6 concept, not official gameplay. Bike trail, Lucia with a python, Vice City at night and a park fight.
#gta6 #gtavi #gta6concept #gaming #shorts
Tags: gta 6, gta vi, gta 6 concept, gta 6 fan made, gta 6 gameplay concept, lucia, jason, vice city
Pinned comment: Will the real GTA 6 look better than this? 👀
```
