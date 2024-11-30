# Совместимый с Willow inference server сервис обработки запросов для Willow устройств
# author: Aleksadr Kumanyaev
from fastapi import Request, FastAPI, HTTPException, Response, APIRouter
import uvicorn
import wave
import base64
from multiprocessing import Process
from transliterate import translit

from starlette.responses import HTMLResponse
from termcolor import cprint
import json
from vacore import VACore
import os
import asyncio

subapi_post = APIRouter()
subapi_get = APIRouter()
modname = os.path.basename(__file__)[:-3] # calculating modname
core = None
model = None

API_WILLOW = "/api/willow"
API_WILLOW_REST = "/api/willow_rest"
API_WILLOW_TTS = "/api/tts"

# функция на старте
def start(core:VACore):
    manifest = { # возвращаем настройки плагина - словарь
        "name": "Willow_is", # имя
        "version": "1.0", # версия
        "require_online": False, # требует ли онлайн?

        "description": "Плагин обработки запросов от Willow (имитирует работу Willow Inference Server)\n"
                       "Если указан input_prefix, то он будет подставляться перед фразой, передаваемой Ирине. Это полезно, если хотите из Willow сразу обращаться к конкретному плагину",
        "default_options": {
            "input_prefix": "ирина",
            "translit": True
        }

    }
    return manifest

def start_with_options(core_local:VACore, manifest:dict):
    global core
    core = core_local
    options = manifest["options"]
    print("options:" + str(options))
    if hasattr(core, 'fastapi'):
        print("Запускаем Willow inference server")
        print("Создаем POST endpoint "+ API_WILLOW)
        core.fastapi.include_router(subapi_post, prefix=f'{API_WILLOW}')

        print("Создаем POST endpoint "+ API_WILLOW_REST)
        core.fastapi.include_router(subapi_post, prefix=f'{API_WILLOW_REST}')

        print("Создаем GET endpoint "+ API_WILLOW_TTS)
        core.fastapi.include_router(subapi_get, prefix=f'{API_WILLOW_TTS}')
    else:
        print("Willow inference server не будет запущен, т.к. не удалось определить режим webapi")
    try:
        import vosk
        from vosk import Model, SpkModel, KaldiRecognizer
        global model
        model = Model("model")
    except Exception as e:
        print("Can't init VOSK - no websocket speech recognition in WEBAPI. Can be skipped")
        import traceback
        traceback.print_exc()
    return

def sendRawTxtOrig(rawtxt:str,returnFormat:str = "none"):
    tmpformat = core.remoteTTS
    core.remoteTTS = returnFormat
    core.remoteTTSResult = ""
    core.lastSay = ""
    isFound = core.run_input_str(rawtxt)
    core.remoteTTS = tmpformat

    if isFound:
        return core.remoteTTSResult
    else:
        return "NO_VA_NAME"

def process_chunk(rec,message,returnFormat):
    # with open('temp/asr_server_test.wav', 'wb') as the_file:
    #     the_file.write(message)

    if message == '{"eof" : 1}':
        return rec.FinalResult()
    elif rec.AcceptWaveform(message):
        res2 = "{}"
        res = rec.Result()
        #print("Result:",res)
        resj = json.loads(res)
        if "text" in resj:
            voice_input_str = resj["text"]
            #print(restext)
            import requests

            if voice_input_str != "" and voice_input_str != None:
                print(voice_input_str)
                #ttsFormatList = ["saytxt"]
                #res2 = sendRawTxtOrig(voice_input_str,"none,saytxt")
                res2 = sendRawTxtOrig(voice_input_str, returnFormat)
                # saywav not supported due to bytes serialization???


                if res2 != "NO_VA_NAME":
                    res3:dict = res2
                    if res3.get("wav_base64") is not None: # converting bytes to str
                        res3["wav_base64"] = res2["wav_base64"].decode("utf-8")
                    res2 = json.dumps(res3)
                else:
                    res2 = "{}"

        else:
            #print("2",rec.PartialResult())
            pass

        return res2
    else:
        res = rec.PartialResult()
        #print("Part Result:",res)
        return rec.PartialResult()

@subapi_post.post('')
async def post_sub(request: Request):
    url_path = request.url.path
    if url_path == API_WILLOW:
        return await willow(request)
    elif url_path == API_WILLOW_REST:
        return await willow_rest(request)  
    return {'i_am': request.url.path}

@subapi_get.get('')
async def get_sub(request: Request):
    url_path = request.url.path
    if url_path == API_WILLOW_TTS:
        return await willow_tts(request)
    return {'i_am': request.url.path}

async def willow(request: Request):
    sample_rate = request.headers.get("x-audio-sample-rate")
    #print("sample_rate: " + sample_rate)
    audio_bits = request.headers.get("x-audio-bits")
    #print("audio-bits: " + audio_bits)
    audio_channel = request.headers.get("x-audio-channel")
    #print("audio-channel: " + audio_channel)
    audio_codec = request.headers.get("x-audio-codec")
    #print("audio-codec: " + audio_codec)
    body = await request.body()
    tmp_wav_name = core.get_tempfilename()
    with wave.open(tmp_wav_name, 'wb') as wavfile:
        wavfile.setparams((int(audio_channel), 2, int(sample_rate), 0, 'NONE', 'NONE'))
        wavfile.writeframes(body)
    with open(tmp_wav_name, "rb") as wav_file:
        wav = wav_file.read()
    if os.path.exists(tmp_wav_name):
        os.unlink(tmp_wav_name)
    global model
    if model != None:
        from vosk import KaldiRecognizer
        rec = KaldiRecognizer(model, int(sample_rate))
        #print("microphone recognition")
        r = process_chunk(rec,wav,"saytxt,saywav")
        #print(r)
        recognized_data = json.loads(r)
        if 'partial' not in recognized_data:
            return toTranslit("не распозналось")
        # print(recognized_data)
        voice_input_str = recognized_data["partial"]
        print(voice_input_str)
        voice_input_str = toTranslit(voice_input_str)
        print(voice_input_str)
        return voice_input_str
    return ""

async def willow_rest(request: Request):
    body = await request.body()
    body_str_translit = body.decode("utf-8")
    body_str_translit = body_str_translit.replace("\"","")
    body_str = fromTranslit(body_str_translit)
    options = core.plugin_options(modname)

    if options["input_prefix"] != "":
       body_str = options["input_prefix"]+ " " + body_str
    #body_str = "домовой " + body_str
    print("willow_rest: " + body_str)
    tmpformat = core.remoteTTS
    core.remoteTTS = "saytxt"
    core.remoteTTSResult = ""
    core.lastSay = ""
    run_res = core.run_input_str(body_str)
    print("run_res:" + str(run_res))
    #core.execute_next(body_str,core.context)
    core.remoteTTS = tmpformat
    res =  core.remoteTTSResult
    print("res:'"+str(res)+"'")
    answer_text = ""
    if res != "":
        answer_text = res["restxt"]
    print("answer_text: " + answer_text)
    #print("runCmd: " + core.remoteTTSResult)
    #return body_str_translit
    return toTranslit(answer_text)

async def willow_tts(request: Request):
    text_translit = request.query_params.get("text")
    text = fromTranslit(text_translit)
    #print("text: " + text)
    tmpformat = core.remoteTTS
    core.remoteTTS = "saywav"
    core.play_voice_assistant_speech(text)
    core.remoteTTS = tmpformat
    res =  core.remoteTTSResult
    #recognized_data = json.loads(r)
    base64_encoded = res["wav_base64"]
    bytes = base64.b64decode(base64_encoded)
    #r = await ttsWav(text)
    #print("r: " + str(base64_encoded))
    return Response(content=bytes, media_type="audio/x-wav")
    #return "xz.wav"

def toTranslit(str):
    options = core.plugin_options(modname)
    if options["translit"] == False:
        return str
    return translit(str, "ru", reversed=True,strict=True)

def fromTranslit(str):
    options = core.plugin_options(modname)
    if options["translit"] == False:
        return str
    return translit(str, "ru", reversed=False,strict=True)