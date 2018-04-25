from proscript import Word, Segment, Proscript
from utilities import utils
from optparse import OptionParser
from pydub import AudioSegment
import os

MAX_SEGMENT_LENGTH = 30.0 #SECONDS
MFA_ALIGN_BINARY = "/Users/alp/extSW/montreal-forced-aligner/bin/mfa_align"
MFA_LEXICON = "/Users/alp/extSW/montreal-forced-aligner/pretrained_models/en.dict"
MFA_LM = "/Users/alp/extSW/montreal-forced-aligner/pretrained_models/english.zip"

SPEAKER_ID = 'spk1'
DEFAULT_AUDIO_EXTENSION = 'wav'
DEFAULT_TRANSCRIPTION_EXTENSION = 'lab'

#creates a proscript and puts in the path
def to_proscript(path, file_ids):
	proscripts = []
	for file_id in file_ids:
		audio_file = os.path.join(path, file_id + '.' + DEFAULT_AUDIO_EXTENSION)
		transcript_file = os.path.join(path, file_id + '.' + DEFAULT_TRANSCRIPTION_EXTENSION)

		audio_stereo = AudioSegment.from_file(audio_file, format=DEFAULT_AUDIO_EXTENSION)

		p = Proscript()
		p.audio_file = audio_file
		p.speaker_ids = [SPEAKER_ID]
		p.id = file_id
		p.duration = audio_stereo.duration_seconds

		#read transcript (only one segment from first line of transcript file)
		f = open(transcript_file, "r")
		transcript = f.readline()
		
		s = Segment()
		s.transcript = transcript
		s.speaker_id = SPEAKER_ID
		s.id = 1
		s.start_time = 0.0
		s.end_time = p.duration

		p.add_segment(s)

		proscripts.append(p)

	aligned_tg_files = utils.mfa_word_align(path, transcript_type="lab", mfa_align_binary=MFA_ALIGN_BINARY, lexicon=MFA_LEXICON, language_model=MFA_LM)

	aligned_tg_files.sort()

	print(aligned_tg_files)

	for p, tg_file in zip(proscripts, aligned_tg_files):
		p.speaker_textgrid_files.append(tg_file)

		utils.get_word_alignment_from_textgrid(p, word_tier_no=0)
		utils.assign_word_ids(p)

		#assign_acoustic_feats
		utils.assign_acoustic_feats(p)

		p.add_end_token()

		output_csv_file = os.path.join(path, p.id + '.csv')

		p.to_csv(output_csv_file, word_feature_set=['id', 'start_time', 'end_time', 'pause_before', 'f0_mean', 'f0_range', 'i0_mean', 'i0_range'], delimiter='|')


def read_files(input_dir=None, audio_file=None, transcription_file=None, transcription=None):
	file_ids = []
	
	if input_dir == None:
		path = os.path.dirname(audio_file)
		file_id, _ = os.path.splitext(os.path.basename(audio_file))
		file_ids.append(file_id)
	else:
		path = input_dir
		for file in os.listdir(path):
			if file.endswith(DEFAULT_AUDIO_EXTENSION):
				audio_file = os.path.join(path, file)
				file_id, _ = os.path.splitext(os.path.basename(audio_file))
				file_ids.append(file_id)
	file_ids.sort()

	return path, file_ids

def asr_to_proscript(audio_file):
	path, file_ids = read_files(audio_file=audio_file)
	to_proscript(path, file_ids)

def main(options):
	if options.audio_file:
		path, file_ids = read_files(audio_file = options.audio_file)
	elif options.input_dir:
		path, file_ids = read_files(input_dir = options.input_dir)

	to_proscript(path, file_ids)

if __name__ == "__main__":
	usage = "usage: %prog [-s infile] [option]"
	parser = OptionParser(usage=usage)

	parser.add_option("-a", "--audio_file", dest="audio_file", default=None, help="audio filename", type="string")
	parser.add_option("-d", "--input_dir", dest="input_dir", default=None, help="directory with wav+lab pairs", type="string")

	(options, args) = parser.parse_args()

	main(options)