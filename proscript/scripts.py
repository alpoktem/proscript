import argparse
import sys
import json
import os
import audioread
from praatio import tgio
from .proscript import Word, Segment, Proscript
from .utilities import utils

DEFAULT_SPEAKER_ID = "SPEAKER1"
DEFAULT_RECORDING_ID = "RECORDING"
DEFAULT_WORKING_DIR = "."
DEFAULT_TXT_OUTPUT_FILENAME = "recording_transcript.txt"
DEFAULT_CSV_OUTPUT_FILENAME = "recording_proscript.csv"

#other parameters
DEFAULT_SEGMENT_END_BUFFER = 0.15

MFA_ALIGN_BINARY = os.getenv('MFA_ALIGN_BINARY')
MFA_LEXICON = os.getenv('MFA_LEXICON')
MFA_LM = os.getenv('MFA_LM')
VOSK_MODEL = os.getenv('VOSK_MODEL') 

#ISSUE 1: MFA processes all audio in the directory of the audio file. 
#ISSUE 2: If audio is in another location, textgrid is placed there, not on working dir 
#ISSUE 3: long overwrites given textgrid, subsequent calls mess it up further

def main():
    parser = argparse.ArgumentParser(prog='PROG')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-r", "--recognize", action='store_true')
    group.add_argument("-s", "--short", action='store_true')
    group.add_argument("-l", "--long", action='store_true')
    parser.add_argument('-a', action="store", dest="audio_path")
    parser.add_argument('-t', action="store", dest="transcript_or_textgrid_path")
    parser.add_argument('-o', action="store", dest="output_dir", default=DEFAULT_WORKING_DIR)

    args = parser.parse_args()

    if not MFA_ALIGN_BINARY or not os.path.exists(MFA_ALIGN_BINARY):
        sys.exit("Cannot locate mfa_align binary as set by environment variable MFA_ALIGN_BINARY")

    if not MFA_LEXICON or not os.path.exists(MFA_LEXICON):
        sys.exit("Cannot locate aligner lexicon as set by environment variable MFA_LEXICON")

    if not MFA_LM or not os.path.exists(MFA_LM):
        sys.exit("Cannot locate aligner language model as set by environment variable MFA_LM")

    if not (args.recognize or args.short or args.long):
        sys.exit("Select one of the options --recognize (-r), --short (-s) or --long (-l)")

    if args.audio_path == None:
        sys.exit("Audio file missing (-a)") 

    if args.recognize:
        if not VOSK_MODEL or not os.path.exists(VOSK_MODEL):
            sys.exit("Cannot locate vosk model directory as set by environment variable VOSK_MODEL")
        else:
            recognize_audio_vosk(args.audio_path, args.output_dir)
        
    elif args.short:
        if not args.transcript_or_textgrid_path == None:
            process_transcripted_shortaudio(args.audio_path, args.transcript_or_textgrid_path, args.output_dir)
        else:
            sys.exit("Transcript file missing (-t)")

    elif args.long:
        if not args.transcript_or_textgrid_path == None:
            process_segmented_longaudio(args.audio_path, args.transcript_or_textgrid_path)
        else:
            sys.exit("Textgrid file missing (-t)")


def get_recording_info(wav_in): 
    return os.path.splitext(os.path.basename(wav_in))[0], os.path.dirname(os.path.abspath(wav_in))   

'''
--recognize
Given audio file with speech, performs ASR and creates proscript file. 
Outputs transcript and proscript.
Depends on vosk-api
Environment variable VOSK_MODEL needs to be set to directory of the vosk ASR model 
'''
def recognize_audio_vosk(audio_path, output_dir):
    from vosk_transcribe import get_recognition

    status, results = get_recognition(audio_path, VOSK_MODEL)

    if not status:
        print("Recognition unsuccessful. Exiting")
        return None
    else:
        audio_id, audio_directory = get_recording_info(audio_path)
        txt_out = os.path.join(output_dir, audio_id + '_transcript.txt')
        csv_out = os.path.join(output_dir, audio_id + '_proscript.csv')

        p = Proscript()
        p.audio_file = audio_path
        p.speaker_ids = [DEFAULT_SPEAKER_ID]
        p.id = audio_id

        try:
            duration = results[-1]['result'][-1]['end'] 
        except:
            duration = 0.0
        print('Audio duration:', duration)

        p.duration = duration

        complete_transcription = ""
        for segment_no, result in enumerate(results):
            s = Segment()
            s.transcript = result['text']
            s.speaker_id = DEFAULT_SPEAKER_ID
            s.id = segment_no + 1
            s.start_time = result['result'][0]['start']
            s.end_time = result['result'][-1]['end']
            p.add_segment(s)
            complete_transcription += s.transcript + " "


        #Write segment information into a textgrid file in the directory of the audio
        utils.proscript_segments_to_textgrid(p, audio_directory, p.id, speaker_segmented=False)

        #Run word alignment software. This will put an extra tier with word boundary information to the textgrid
        try:
            utils.mfa_word_align(audio_directory, mfa_align_binary=MFA_ALIGN_BINARY, lexicon=MFA_LEXICON, language_model=MFA_LM)
            mfa_failed = False
        except Exception as e:
            print(e)
            mfa_failed = True

        if not mfa_failed:
            #Get word boundary info in textgrid to proscript, do word-level feature annotation 
            utils.get_word_features_from_textgrid(p, prosody_tag=True, remove_textgrid=False)
            utils.assign_word_ids(p)

            p.get_speaker_means() #necessary step
            utils.assign_acoustic_means(p) #normalize acoustic measurements w.r.t the speaker's norm

            #write transcription to text file
            with open(txt_out, 'w') as f:
                f.write(complete_transcription.strip())

            #write proscript to csv
            p.to_csv(csv_out)
            return csv_out
        else: 
            print("MFA failed")
            return None

'''
--short
Creates proscript from a short audio of max 30s with known transcript specified in a text file. 
Transcription should only contain word tokens (no punctuation etc.)
Outputs proscript
'''
def process_transcripted_shortaudio(audio_path, transcript_path, working_dir=DEFAULT_WORKING_DIR):

    #read transcript into memory
    with open(transcript_path, 'r') as f:
        complete_transcription = f.read()
    print("Audio transcript: %s"%complete_transcription)

    #output files
    audio_id, audio_directory = get_recording_info(audio_path)

    csv_out = os.path.join(working_dir, audio_id + '_proscript.csv')

    #get duration
    with audioread.audio_open(audio_path) as f:
        duration = f.duration
    
    p = Proscript()
    p.audio_file = audio_path
    p.speaker_ids = [DEFAULT_SPEAKER_ID]
    p.id = audio_id
    p.duration = duration

    #Since it's a short recording, the whole recording will consist of one segment. 
    #Create a segment, put the whole transcription inside and define it's boundaries
    s = Segment()
    s.transcript = complete_transcription
    s.speaker_id = DEFAULT_SPEAKER_ID
    s.id = 1
    s.start_time = 0.0
    s.end_time = duration
    p.add_segment(s)

    #Write segment information into a textgrid file in the directory of the audio
    utils.proscript_segments_to_textgrid(p, audio_directory, p.id, speaker_segmented=False)

    #Run word alignment software. This will put an extra tier with word boundary information to the textgrid
    try:
        utils.mfa_word_align(audio_directory, mfa_align_binary=MFA_ALIGN_BINARY, lexicon=MFA_LEXICON, language_model=MFA_LM)
        mfa_failed = False
    except Exception as e:
        print("MFA Failed", e)
        mfa_failed = True

    if not mfa_failed:
        #Get word boundary info in textgrid to proscript, do word-level feature annotation 
        utils.get_word_features_from_textgrid(p, prosody_tag=True, remove_textgrid=False)
        utils.assign_word_ids(p)

        p.get_speaker_means() #necessary step
        utils.assign_acoustic_means(p) #normalize acoustic measurements w.r.t the speaker's norm

        #write proscript to csv
        p.to_csv(csv_out)
        return csv_out, complete_transcription
    else: 
        print("MFA failed")
        return None, None

'''
--long
Creates a proscript from an audio file with textgrid. 
Textgrid needs to contain sentence boundaries marked.
Outputs proscript
'''
def process_segmented_longaudio(audio_path, textgrid_path, working_dir=DEFAULT_WORKING_DIR):
    audio_id, audio_directory = get_recording_info(audio_path)
    csv_out = os.path.join(working_dir, audio_id + '_proscript.csv')

    #read segments from textgrid to proscript
    textgrid = tgio.openTextgrid(textgrid_path)
    segment_tier = textgrid.tierDict[textgrid.tierNameList[0]]

    p = Proscript()
    p.audio_file = audio_path
    p.textgrid_file = textgrid_path
    p.speaker_ids = [DEFAULT_SPEAKER_ID]
    p.id = "audio_id"

    for interval in segment_tier.entryList:    
        seg = Segment()
        seg.speaker_id = DEFAULT_SPEAKER_ID
        seg.start_time = interval.start
        seg.end_time = interval.end
        seg.transcript += interval.label
        p.add_segment(seg)


    mfa_failed = False
    try:
        utils.mfa_word_align_audio_and_textgrid(audio_path, textgrid_path, mfa_align_binary=MFA_ALIGN_BINARY, lexicon=MFA_LEXICON, language_model=MFA_LM)
    except Exception as e:
        print(e)
        mfa_failed = True

    if not mfa_failed:
        #Get word boundary info in textgrid to proscript, do word-level feature annotation 
        utils.get_word_features_from_textgrid(p, prosody_tag=True, remove_textgrid=False)
        utils.assign_word_ids(p)

        p.get_speaker_means() #necessary step
        utils.assign_acoustic_means(p) #normalize acoustic measurements w.r.t the speaker's norm

        #write proscript to csv
        p.to_csv(csv_out)
        return csv_out
    
    else:
        print("MFA failed")
        return None


    
if __name__ == '__main__':
    main()