# Proscript

A Python package for creating proscript files. Proscript helps represent speech with segment-level prosodic features like f0, intensity and word alignment. 

## System dependencies

Proscript is developed and tested on a MacOS with Python 3+. 

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

3- Install Montreal Forced aligner and set the following environment variables for the scripts to locate binaries and models of Montreal Forced Aligner
```
export MFA_ALIGN_BINARY=montreal-forced-aligner-path/bin/mfa_align
export MFA_LEXICON=montreal-forced-aligner-path/pretrained_models/en.dict
export MFA_LM=montreal-forced-aligner-path/pretrained_models/english.zip
```

## Endpoint usage

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

Does automatic speech recognition and then creates a proscript of it. 

Set environment variable for the Vosk model you want to use by:

```
export VOSK_MODEL=vosk-model-path
```

```
proscripter --recognize -a audio.wav -o output_dir
```

## Library usage

Refer to `proscript/scripts.py` to see examples of creating proscript files. 

Reading a proscript file in python:

```
from proscript import Proscript

p = Proscript()
p.from_file(csv_filename='my_proscript.csv', proscript_id="my_proscript", audio_file="my_audio.wav", delimiter="|")
```

## Libraries that use Proscript

- [Movie2parallelDB](https://github.com/alpoktem/movie2parallelDB) makes sentence aligned proscripts from subtitled and dubbed movies.
- [Prosograph](https://github.com/alpoktem/Prosograph) lets visualize proscripts.
- [PunkProse](https://github.com/alpoktem/punkProse) generates punctuation for speech transcripts using lexical, syntactic and prosodic features stored in proscript files.

## Citation

If you use this library, please cite the following paper:

```
Alp Öktem, Mireia Farrús, Antonio Bonafonte. Corpora Compilation for Prosody-informed Speech Processing. Lang Resources & Evaluation (Accepted). 
```
