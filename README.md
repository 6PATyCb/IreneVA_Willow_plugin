# IreneVA_Willow_plugin
Плагин для голосового помошника [Ирины](https://github.com/janvarev/Irene-Voice-Assistant), позволяющий обрабатывать запросы от устройств ESP32-S3-BOX3 с прошивкой [Willow](https://github.com/toverainc/willow) (имитирует работу Willow Inference Server). Как выглядят устройства вы можете посмотреть [здесь](https://heywillow.io/hardware/).

-----------------------

UPD: Я выпустил несколько переработанных прошивок для `Willow`, которые можно использовать не только для `ESP32-S3-BOX3`, но и для `JC3636W518EN`, подробнее смотрите [здесь](https://github.com/6PATyCb/willow/releases). Используя эти прошивки для устройств или даже просто используя мобильное приложение `HA`, а также мои плагины для `Home Assistant` ([раз](https://github.com/6PATyCb/irene_stt) и [два](https://github.com/6PATyCb/irene_tts)) можно использовать `Ирину` как локальную обработку по преобразованию голоса в голосовые комманды и озвучиванию ответов в `HA` в механизме `assist`. 

Если вы решили использовать Willow устройство в качестве микрофона и динамика для HA, то нужно в `WAS`, в качестве взаимодействия выбирать натройки, как на скриншоте ниже (192.168.144.112:5003 - это мой сервер `Ирины` и на нем же на порту 8123 висит `HA`):

![photo_2025-03-18_03-40-37](https://github.com/user-attachments/assets/de81550d-8a63-4afd-8ec1-6b44b104081a)

А в самом `HA` у вас должны быть настроены STT и TTS:

![photo_2025-03-18_03-24-27](https://github.com/user-attachments/assets/64a6ed8d-4f20-47b9-8eae-7a2face3d39e)


-----------------------
Устройство может выступать в качестве приема команд для Ирины и озвучивать ее ответы. Также можно использовать устройство для управления умным домом через Home Assistant (потребуется [плагин](https://github.com/6PATyCb/IreneVA-hassio-script-trigger-plugin)). 

## Как использовать плагин
Плагин использует Webapi. Из-за этого он работает только в режиме, когда Ирина запущена в режиме Webapi (сервер с несколькими клиентами, есть веб-интерфейс).

1. Для работы требуется `Ирина` не ниже `10.9.3`
2. Скачайте репозиторий и положите папку plugins в директорию с репозиторием Ирины (или просто положите файл в plugins)
3. Измените в настройках файла `runva_webapi_docker.json` значение `host` на `0.0.0.0`, чтобы устройство Willow могло подключиться к вашему ПК.
4. (Необязательный) установите модуль `transliterate` для python `pip install transliterate`. Это позволит отображать русский текст на экране устройства т.к. на данный момент в нем поддержка только латинских букв при отображении (UPD: Мне удалось [допилить](https://github.com/6PATyCb/willow) прошивку Willow чтобы интерфейс был на русском). 
5. Запустите `runva_webapi.py` или `start-webapi.bat` если вы использовали установку Ирины для [Windows](https://github.com/janvarev/Irene-VA-win-installer)

Также для работы нужно выполнить переконфигурацию Willow устройства через [WAS](https://github.com/toverainc/willow-application-server).

Далее 127.0.0.1 - должен быть заменен на IP вашего ПК, к которому будет подключаться устройство Willow. В моем [примере](https://github.com/6PATyCb/IreneVA_Willow_plugin/blob/main/was.jpg) это IP `192.168.133.252`

На странице настроек `WAS` указать:

`Willow Inference Server Speech Recognition URL` - `http://127.0.0.1:5003/api/willow`

`Willow Audio Response Type` - `Text to Speech`

`Willow Inference Server Text to Speech URL` - `http://127.0.0.1:5003/api/tts`

`Command Endpoint` - `REST`

`REST URL` - `http://127.0.0.1:5003/api/willow_rest`

Обратите внимание, что если в файле настроек `runva_webapi_docker.json` значение `use_ssl` = `true`, то и все ссылки выше, которые указываются в `WAS` для `Willow` устройства, должны начинаться не с `http`, а с `https`.


## Принцип работы
Устройство `ESP32-S3-BOX` с прошивкой `Willow` в своей работе полагается на две основных вещи - сервер `WAS` (Используется для настройки устройств) и сервер `WIS` (используется для обработки голоса в текст и обратно). Устройство постоянно слушает свой микрофон и использует маленькую нейронку `ESP-SR`, которая распознает слово-активатор (`wake word`) и после этого передает услышанную фразу на сервер `WIS`, чтобы преобразовать ее в текст. Этот процесс выполняется через вызов (1) сервиса по ссылке `Willow Inference Server Speech Recognition URL`. Ответ будет содержать распознанный текст команды, который устройство сразу отображает на экране и по нему можно понять насколько корректно услышанное распозналось. Сразу после получения этого ответа, устройство делает вызов (2) по ссылке `REST URL`, куда передает распознанный текст команды и ждет оттуда ответ с текстом, который будет содержать результат выполнения команды. Сразу после получения текста выполнения команды, он отображается на экране и отправляется через вызов (3) по ссылке `Willow Inference Server Speech Recognition URL`, где происходит его преобразование в голос и формируется ответ в виде аудиозаписи, которая озвучивается через динамик устройства.

Данный плагин создает свои собственные ссылки для вызовов (1), (2) и (3), которые используют внутри себя возможности Ирины по преобразованию голоса в текст, по выпонению команд и по преобразованию текста в голос. Эти ссылки для вызовов начинают работать, если вы запускаете Ирину в режиме Webapi (`runva_webapi.py`). Т.к. слово-активатор (Я использую слово `Алекса`) срабатывает на самом устройстве, у плагина есть параметр `input_prefix` в файле `options/plugin_willow_is.json` (файл создастся автоматически при первом запуске плагина), который позволяет задать активационное слово в контексте команд Ирины. По умолчанию это как раз слово `ирина` (важно слово писать маленькими буквами). 

Для примера: Я говорю `"Алекса привет"`. Устройство распознает `"Алекса"`, как слово-активатор, а текст `"привет"` заменяет, как `input_prefix` + `" привет"`, т.е. в Ирину уже приходит команда `"ирина привет"`. Ирина на нее отвечает текстом `"и тебе привет"`, который возвращается в виде текста ответа на устройство и его устройство дополнительно обратно засылает в Ирину для преобразования в голос и проигрывает через свой динамик, озвучивая `"и тебе привет"`.

Также в файле настроек есть возможность все ответы сервисов возвращать в устройство в виде транслита. Это вынужденная мера, т.к. устройство на своем экране позволяет отображать только латинские буквы. Регулируется это параметром `translit`.

## Как использовать с Home Assistant

Я подразумеваю, что у вас уже есть Willow устройство у которого ссылки настроены как описано выше, а также у вас есть текущий плагин версии 2.0 или выше и настроенный [плагин](https://github.com/6PATyCb/IreneVA-hassio-script-trigger-plugin) для работы с HomeAssistant


Чтобы всё работало как надо, в основном конфиге Ирины `options/core.json` в конце файла нужно сделать следующие изменения 
```JSON
{
    ...
    "voiceAssNameRunCmd": {
        "домовой": "хочу"
    },
    "voiceAssNames": "ирина|ирины|ирину|домовой"
}
```
Эти изменения позволят по имени `домовой` (у меня это имя для Home Assistant) подставлять ключевую фразу `хочу` для активации работы плагина Home Assistant.

Далее нужно исправить конфиг текущего плагина `options/plugin_willow_is.json`
```JSON
{
    "input_prefix": "домовой",
    "postfix_by_ip": {
        "192.168.144.12": "на кухне",
        "192.168.144.14": "в зале"
    },
    "translit": true,
    "v": "2.0"
}
```
`input_prefix` если не пустой, то позволяет сразу подставлять этот текст в начало фразы для Ирины, т.е. если ваше Willow устройство используется только для управления Home Assistant, то вам не придется говорить каждый раз `домовой`.

Блок `postfix_by_ip` не является обязательным, но позволяет для конкретного вашего Willow устройства (если у вас их больше одного) указать текст, который автоматически подставится в конце фразы для Ирины. Это позволяет настроить скрипты для Home Assistant так, чтобы в разных помещениях, обращаясь к вашему Willow устройству, одна и та же фраза преобразовывалась в разный текст. Для примера: фраза `открой окно`, для `192.168.144.12` будет звучать как `открой окно на кухне`, а для `192.168.144.14`, как `открой окно в зале`.



