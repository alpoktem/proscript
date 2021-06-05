"""
Proscript conversion scripts

Usage:
	proscripter [-l|-s]
	
"""
import argparse
import sys
import json
import os
from proscript import Word, Segment, Proscript
#from utilities import utils #FOR DEVELOPMENT
from proscript.utilities import utils

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

#ISSUE 1: MFA processes all audio in the directory of the audio file. 
#ISSUE 2: If audio is in another location, textgrid is placed there, not on working dir 

def main():
	parser = argparse.ArgumentParser(prog='PROG')
	group = parser.add_mutually_exclusive_group()
	group.add_argument("-r", "--recognize_audio", action='store_true')
	group.add_argument("-x", "--recognize_audio_google", action='store_true')
	group.add_argument("-s", "--process_shortaudio", action='store_true')
	group.add_argument("-l", "--process_longaudio", action='store_true')
	parser.add_argument('-a', action="store", dest="audio_path")
	parser.add_argument('-c', action="store", dest="credentials_path")
	parser.add_argument('-t', action="store", dest="transcript_path")
	parser.add_argument('-g', action="store", dest="textgrid_path")

	args = parser.parse_args()

	if not MFA_ALIGN_BINARY or not os.path.exists(MFA_ALIGN_BINARY):
		sys.exit("Cannot locate mfa_align binary as set by environment variable MFA_ALIGN_BINARY")

	if not MFA_LEXICON or not os.path.exists(MFA_LEXICON):
		sys.exit("Cannot locate aligner lexicon as set by environment variable MFA_LEXICON")

	if not MFA_LM or not os.path.exists(MFA_LM):
		sys.exit("Cannot locate aligner language model as set by environment variable MFA_LM")

	if args.audio_path == None:
		sys.exit("Audio file missing (-a)")	

	if args.recognize_audio_google:
		if not args.credentials_path == None:
			recognize_audio_google(args.audio_path, args.credentials_path)
		else:
			sys.exit("Specify credentials file (-c) for recognition")
	elif args.recognize_audio:
		recognize_audio_vosk()
	elif args.process_shortaudio:
		if not args.transcript_path == None:
			process_transcripted_shortaudio(args.audio_path, args.transcript_path)
		else:
			sys.exit("Transcript file missing (-t)")

	elif args.process_longaudio:
		if not args.textgrid_path == None:
			process_segmented_longaudio("lala", "lala")
		else:
			sys.exit("Textgrid file missing (-g)")

	else:
		sys.exit("Possible actions:\n--recognize_audio(-r)\n--process_shortaudio(-s)\n--process_longaudio(-l)")


def get_recording_info(wav_in): 
	return os.path.splitext(os.path.basename(wav_in))[0], os.path.dirname(os.path.abspath(wav_in))   

def recognize_audio_vosk():
	print("Not yet implemented")

def recognize_audio_google(audio_path, credentials_json_file, working_dir=DEFAULT_WORKING_DIR, segment_end_buffer=DEFAULT_SEGMENT_END_BUFFER):
	'''
		Creates proscript from result of recognition. Uses Google Cloud Speech API. 
		Not tested
	'''

	import speech_recognition as sr
	
	#read google cloud speech credentials
	with open (credentials_json_file, 'r') as f: 
		google_cloud_speech_credentials = f.read()


	#output files
	audio_id, audio_directory = get_recording_info(audio_path)

	txt_out = os.path.join(working_dir, audio_id + '_transcript.txt')
	csv_out = os.path.join(working_dir, audio_id + '_proscript.csv')

	#Load recognition tools
	recognizer = sr.Recognizer()

	print("Sending audio to Google Cloud speech API")
	with sr.AudioFile(audio_path) as source:
		audio = recognizer.record(source)  # read the entire audio file
	try:
		response = recognizer.recognize_google_cloud(audio, credentials_json=google_cloud_speech_credentials, show_all=True)
	except sr.RequestError as e:
		print("Could not request results from Google Cloud service; {0}".format(e))
		response = None

	#Convert response to proscript
	if response:
		duration = len(audio.frame_data) / audio.sample_rate / audio.sample_width
		print('Audio duration:', duration)
		
		p = Proscript()
		p.audio_file = audio_path
		p.speaker_ids = [DEFAULT_SPEAKER_ID]
		p.id = audio_id
		p.duration = duration

		#Parse ASR response to segments
		complete_transcription = ""
		for segment_no, recognized_segment in enumerate(response['results']):
			transcription = recognized_segment['alternatives'][0]['transcript']
			confidence = recognized_segment['alternatives'][0]['confidence']
			wordData = recognized_segment['alternatives'][0]['words']
			s = Segment()
			s.transcript = transcription
			s.speaker_id = DEFAULT_SPEAKER_ID
			s.id = segment_no + 1
			s.start_time = float(wordData[0]['startTime'][:-1])
			s.end_time = float(wordData[-1]['endTime'][:-1]) + segment_end_buffer
			p.add_segment(s)
			complete_transcription += transcription + " "

		print("Google Cloud recognized: %s"%complete_transcription)

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
				f.write(complete_transcription)

			#write proscript to csv
			p.to_csv(csv_out)
			return csv_out, complete_transcription
		else: 
			print("MFA failed")
			return None, None
	else:
		print("ASR cannot recognize audio")
		return None, None

def process_transcripted_shortaudio(audio_path, transcript_path, working_dir=DEFAULT_WORKING_DIR):
	'''
		Creates proscript from a short audio of max 30s with known transcript specified in a text file. 
		Transcription should only contain word tokens (no punctuation etc.)
	'''
	#read transcript into memory
	with open(transcript_path, 'r') as f:
		complete_transcription = f.read()
	print("Audio transcript: %s"%complete_transcription)


	#output files
	audio_id, audio_directory = get_recording_info(audio_path)

	csv_out = os.path.join(working_dir, audio_id + '_proscript.csv')

	recognizer = sr.Recognizer()
	with sr.AudioFile(audio_path) as source:
		audio = recognizer.record(source)  # read the entire audio file

	#Put segment transcript into a proscript
	duration = len(audio.frame_data) / audio.sample_rate / audio.sample_width
	print('Audio duration:', duration)
	
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
		return csv_out, complete_transcription
	else: 
		print("MFA failed")
		return None, None


def process_segmented_longaudio(audio_path, textgrid_path):
	'''
	STUB
	'''

	print("Not implemented yet.")
	
if __name__ == '__main__':
	main()