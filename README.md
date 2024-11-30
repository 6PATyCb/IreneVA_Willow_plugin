# IreneVA_Willow_plugin
Плагин для голосового помошника [Ирины](https://github.com/janvarev/Irene-Voice-Assistant), позволяющий обрабатывать запросы от устройств ESP32-S3-BOX с прошивкой [Willow](https://github.com/toverainc/willow) (имитирует работу Willow Inference Server). Как выглядят устройства вы можете посмотреть [здесь](https://heywillow.io/hardware/).

Устройство может выступать в качестве приема команд для Ирины и озвучивать ее ответы. Также можно использовать устройство в для управления умным домом через Home Assistant (потребуется [плагин](https://github.com/6PATyCb/IreneVA-hassio-script-trigger-plugin)). 

## Как использовать плагин
Плагин использует Webapi. Из-за этого он работает только в режиме, когда Ирина запущена в режиме Webapi (сервер с несколькими клиентами, есть веб-интерфейс).

1. Для работы требуется `Ирина` не ниже `10.9.3`
2. Скачайте репозиторий и положите папку plugins в директорию с репозиторием Ирины (или просто положите файл в plugins)
3. Измените в настройках файла `runva_webapi_docker.json` значение `host` на `0.0.0.0`, чтобы устройство Willow могло подключиться к вашему ПК.
4. (Необязательный) установите модуль `transliterate` для python `pip install transliterate`. Это позволит отображать русский текст на экране устройства т.к. на данный момент в нем поддержка только латинских букв при отображении.
5. Запустите `runva_webapi.py` или `start-webapi.bat` если вы использовали установку Ирины для [Windows](https://github.com/janvarev/Irene-VA-win-installer)

Также для работы нужно выполнить переконфигурацию Willow устройства через [WAS](https://github.com/toverainc/willow-application-server).

Далее 127.0.0.1 - должен быть заменен на IP вашего ПК, к которому будет подключаться устройство Willow. В моем [примере](https://github.com/6PATyCb/IreneVA_Willow_plugin/blob/main/was.jpg) это IP `192.168.133.252`

На странице настроек `WAS` указать:

`Willow Inference Server Speech Recognition URL` - `http://127.0.0.1:5003/api/willow`

`Willow Audio Response Type` - `Text to Speech`

`Willow Inference Server Text to Speech URL` - `http://127.0.0.1:5003/api/tts`

`Command Endpoint` - `REST`

`REST URL` - `http://127.0.0.1:5003/api/willow_rest`


## Принцип работы
Будет дописано чуть позже
