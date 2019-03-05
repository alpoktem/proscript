"""Proscript conversion scripts

Usage:
    proscripter [-l|-s]
    
"""
import argparse
from proscript import Word, Segment, Proscript
from proscript.utilities import utils


def main():
	usage = "usage: %prog [-s infile] [option]"
	parser = argparse.ArgumentParser(prog='PROG', usage=usage)
	group = parser.add_mutually_exclusive_group()
	group.add_argument("-r", "--recognize_audio", action='store_true')
	group.add_argument("-s", "--process_shortaudio", action='store_true')
	group.add_argument("-l", "--process_longaudio", action='store_true')

	args = parser.parse_args()

	if args.recognize_audio:
		recognize_audio("lala")
	elif args.process_shortaudio:
		process_transcripted_shortaudio("lala", "lala")
	elif args.process_longaudio:
		process_segmented_longaudio("lala", "lala")

def recognize_audio(audio_path):
	p = Proscript()
	p.id = "recognize_audio"
	print(p.id)

def process_transcripted_shortaudio(audio_path, transcript_path):
	p = Proscript()
	p.id = "process_transcripted_shortaudio"
	print(p.id)

def process_segmented_longaudio(audio_path, textgrid_path):
	p = Proscript()
	p.id = "process_segmented_longaudio"
	print(p.id)
	
if __name__ == '__main__':
	main()