from vosk import Model, KaldiRecognizer, SetLogLevel
import wave
import json
import subprocess

SetLogLevel(0)

CONFIDENCE_THRESHOLD = 0.8
SAMPLE_RATE=16000

def get_recognition(audio_path, vosk_model_path):
    model = Model(vosk_model_path)
    rec = KaldiRecognizer(model, SAMPLE_RATE)

    try:
        process = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                                    audio_path,
                                    '-ar', str(SAMPLE_RATE) , '-ac', '1', '-f', 's16le', '-'],
                                    stdout=subprocess.PIPE)
        converted = True
    except:
        print("WARNING: ffmpeg not found in system")
        converted = False

        wf = wave.open(audio_path, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            print ("ERROR: Can't do conversion without ffmpeg. Audio file must be WAV format mono PCM.")
            return 0, []

    results = []
    words = []
    while True:
        if converted:
            data = process.stdout.read(4000)
        else:
            data = wf.readframes(4000)

        if len(data) == 0:
           break
        if rec.AcceptWaveform(data):
           segment_result = json.loads(rec.Result())
           
           results.append(segment_result)
           words.extend(segment_result['result'])
    final_result = json.loads(rec.FinalResult())
    results.append(final_result)
    if 'result' in final_result:
        words.extend(final_result['result'])
    
    return 1, results

