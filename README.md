# Proscript

A Python package for creating proscript files. Proscript helps represent speech with segment-level prosodic features like f0, intensity and word alignment. 

## System dependencies

Proscript is developed and tested on a MacOS with Python 3+. Speech recognition feature only works in Linux. 

Proscript depends on the following libraries:

- [Praat](http://www.fon.hum.uva.nl/praat/)
- [Montreal forced aligner](https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner)
- [vosk-api](https://github.com/alphacep/vosk-api)
- [praatio](https://github.com/timmahrt/praatIO)

## Installation

1- Install Praat and make sure it is accessible from command line as `praat`.

2- Install proscript

```
git clone https://github.com/alpoktem/proscript.git
cd proscript
pip install .
```

3- Install Montreal Forced aligner and make sure environment variables are set for locating binaries and models for Montreal Forced Aligner
```
export MFA_ALIGN_BINARY=/Users/alp/extSW/montreal-forced-aligner/bin/mfa_align
export MFA_LEXICON=/Users/alp/extSW/montreal-forced-aligner/pretrained_models/en.dict
export MFA_LM=/Users/alp/extSW/montreal-forced-aligner/pretrained_models/english.zip
```

## Usage

### Process short audio with transcription

Creates proscript from a short audio of max 30s with known transcript specified in a text file. Transcription should only contain word tokens (no punctuation etc.)

```
proscripter --short -a audio.wav -t transcript.txt -o output_dir
```

### Process audio with segmented textgrid

Creates proscript from an audio with a segmented transcript specified in a TextGrid file. 

```
proscripter --long -a audio.wav -t audio.TextGrid -o output_dir
```

### Process audio using Vosk speech recognizer

Set environment variable for the Vosk model you want to use

```
export VOSK_MODEL=/Users/alp/Documents/TWB/play/apicilik/Gamayun-API/asr-api/models/vosk-model-small-en-us-0.15
```

```
proscripter --recognize -a audio.wav -o output_dir
```
