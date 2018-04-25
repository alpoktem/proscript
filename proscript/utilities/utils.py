# -*- coding: utf-8 -*-
from praatio import tgio
import io
import os
import sys
import tempfile
import subprocess
import re
import csv
import json
import math
from proscript import Word
from proscript import Proscript
from proscript import Segment
from collections import OrderedDict
import numpy as np
import nltk
from shutil import copyfile

ENTRY_MERGE_LIMIT = 0.1

FLOAT_FORMATTING="{0:.4f}"
TIME_PRECISION = 3
CONTOUR_BIN_NO=10

END = "<END>"

#writes segment information in proscript to textgrid
def proscript_segments_to_textgrid(proscript, output_dir, file_prefix="", speaker_segmented=False):
	output_files = []
	assert proscript.duration > 0.0
	for speaker_index, speaker_id in enumerate(proscript.speaker_ids):
		tg = tgio.Textgrid()

		if speaker_segmented:
			segment_entry_list = [(segment.start_time, segment.end_time, segment.transcript) for segment in proscript.get_speaker_segments(speaker_id)]
		else:
			segment_entry_list = [(segment.start_time, segment.end_time, segment.transcript) for segment in proscript.segment_list]
		segment_tier = tgio.IntervalTier('%s'%speaker_id, segment_entry_list, 0, proscript.duration)

		tg.addTier(segment_tier)

		try:
			textgrid_file = proscript.speaker_textgrid_files[speaker_index]
		except:
			if speaker_segmented:
				textgrid_file = os.path.join(output_dir, "%s-%s.TextGrid"%(file_prefix, speaker_id))
			else:
				textgrid_file = os.path.join(output_dir, "%s.TextGrid"%(file_prefix))

		saveTextGridWithTags(tg, textgrid_file)
		output_files.append(textgrid_file)
		proscript.speaker_textgrid_files.append(textgrid_file)

def saveTextGridWithTags(textgrid, fn, minimumIntervalLength=tgio.MIN_INTERVAL_LENGTH):
	for tier in textgrid.tierDict.values():
		tier.sort()
	# Fill in the blank spaces for interval tiers
	for name in textgrid.tierNameList:
		tier = textgrid.tierDict[name]
		if isinstance(tier, tgio.IntervalTier):
			tier = tgio._fillInBlanks(tier, "", textgrid.minTimestamp, textgrid.maxTimestamp)
		if minimumIntervalLength is not None:
			tier = tgio._removeUltrashortIntervals(tier, minimumIntervalLength)
		textgrid.tierDict[name] = tier

	for tier in textgrid.tierDict.values():
		tier.sort()

	# Header
	outputTxt = ''
	outputTxt += 'File type = "ooTextFile"\n'
	outputTxt += 'Object class = "TextGrid"\n\n'
	outputTxt += "xmin = %s\nxmax = %s\n" % (repr(textgrid.minTimestamp), repr(textgrid.maxTimestamp))
	outputTxt += "tiers? <exists>\nsize = %d\n" % len(textgrid.tierNameList)
	outputTxt += "item []:\n"
	for tierNo, tierName in enumerate(textgrid.tierNameList):
		tierId = tierNo + 1
		outputTxt += "\titem [%d]:\n" % tierId
		outputTxt += getTierAsTextWithTags(textgrid.tierDict[tierName])

	with io.open(fn, "w") as fd:
		fd.write(outputTxt)

def getTierAsTextWithTags(tier):
	'''Prints each entry in the tier on a separate line w/ timing info'''
	text = ""
	text += '\t\tclass = "%s"\n' % tier.tierType
	text += '\t\tname = "%s"\n' % tier.name
	text += '\t\txmin = %s\n\t\txmax = %s\n\t\tintervals: size = %s\n' % (repr(tier.minTimestamp), repr(tier.maxTimestamp), len(tier.entryList))

	for entryNo, entry in enumerate(tier.entryList):
		entryId = entryNo + 1
		entry = [repr(val) for val in entry[:-1]] + ['"%s"' % entry[-1], ]
		try:
			unicode
		except NameError:
			unicodeFunc = str
		else:
			unicodeFunc = unicode
		text += "\t\t\tintervals [%d]:\n" %entryId
		#text += "\n\t\t\t".join([unicodeFunc(val) for val in entry]) + "\n"
		text += "\t\t\t\txmin = %s\n" % unicodeFunc(entry[0])
		text += "\t\t\t\txmax = %s\n" % unicodeFunc(entry[1])
		text += "\t\t\t\ttext = %s\n" % unicodeFunc(entry[2])
	return text

def find_file(name, extension, path):
	filename = name + '.' + extension
	for root, dirs, files in os.walk(path):
		if filename in files:
			return os.path.join(root, filename)
	return None

#Creates word/phoneme alignments in the textgrids in the input_textgrid_directory using Montreal Forced Aligner. 
#Requirement: Input textgrids are already segmented into max 30 second intervals.
#Warning: Replaces the input textgrids with word aligned textgrids.
#TODO: work with lab files 
def mfa_word_align(input_textgrid_directory, transcript_type="TextGrid", merge_textgrids=True, mfa_align_binary=None, lexicon=None, language_model=None, temp_dir=None):
	#create a temporary output directory
	if temp_dir == None:
		temp_dir = tempfile.mkdtemp()
	elif not os.path.exists(temp_dir):
		os.makedirs(temp_dir)

	segmented_textgrids = []
	
	print("Temp directory for MFA: %s"%temp_dir)

	#call mfa for the input textgrid folder and temp output
	print("Sending Textgrids to Montreal Forced Aligner")

	command = "%s %s %s %s %s"%(mfa_align_binary, input_textgrid_directory, lexicon, language_model, temp_dir)
	p = subprocess.Popen(command.split())
	p.communicate()

	#merge output textgrids and input textgrids/transcriptions
	for root, direc, files in os.walk(temp_dir):
		for file in files:
			if file.endswith(".TextGrid"):
				segmented_tg_file = os.path.join(root, file)
				segmented_tg_file_basename = os.path.splitext(os.path.basename(segmented_tg_file))[0]
				#print("segmented: %s"%segmented_tg_file)
				
				if merge_textgrids and transcript_type == "TextGrid":
					segmented_tg = tgio.openTextgrid(segmented_tg_file)
					word_tier = segmented_tg.tierDict[segmented_tg.tierNameList[0]]
					phoneme_tier = segmented_tg.tierDict[segmented_tg.tierNameList[1]]
					#get segment info from unsegmented textgrid
					unsegmented_tg_file = find_file(segmented_tg_file_basename, "TextGrid", input_textgrid_directory)
					#print("unsegmented: %s"%unsegmented_tg_file)
					unsegmented_tg = tgio.openTextgrid(unsegmented_tg_file)
					segment_tier = unsegmented_tg.tierDict[unsegmented_tg.tierNameList[0]]
					#merge_adjacent_segments(segment_tier)

					new_tg = tgio.Textgrid()

					new_tg.addTier(segment_tier)
					new_tg.addTier(word_tier)
					new_tg.addTier(phoneme_tier)

					saveTextGridWithTags(new_tg, unsegmented_tg_file)
					segmented_textgrids.append(unsegmented_tg_file)
				elif merge_textgrids and transcript_type == "lab":
					segmented_tg = tgio.openTextgrid(segmented_tg_file)
					word_tier = segmented_tg.tierDict[segmented_tg.tierNameList[0]]
					phoneme_tier = segmented_tg.tierDict[segmented_tg.tierNameList[1]]
					#get segment info from lab file
					lab_transcript_file = find_file(segmented_tg_file_basename, "lab", input_textgrid_directory)
					with open(lab_transcript_file, 'r') as myfile:
						segment_transcript=myfile.read()
					segment_tier = tgio.IntervalTier('segment', [(word_tier.entryList[0].start, word_tier.entryList[-1].end, segment_transcript)], segmented_tg.minTimestamp, segmented_tg.maxTimestamp)
					new_tg = tgio.Textgrid()

					new_tg.addTier(segment_tier)
					new_tg.addTier(word_tier)
					new_tg.addTier(phoneme_tier)

					output_textgrid_file = os.path.join(input_textgrid_directory, segmented_tg_file_basename + '.TextGrid')
					saveTextGridWithTags(new_tg, output_textgrid_file)
					segmented_textgrids.append(output_textgrid_file)
				else:
					#Don't merge
					segmentation_tg_file = os.path.join(input_textgrid_directory, file)
					copyfile(segmented_tg_file, segmentation_tg_file)
					segmented_textgrids.append(segmentation_tg_file)
	return segmented_textgrids


def readTedDataToMemory(word_id_list, file_wordalign=None, file_wordaggs_f0=None, file_wordaggs_i0=None, dir_raw_f0=None, dir_raw_i0=None):
	#read wordaggs_f0 file to a dictionary 
	word_id_to_f0_features_dic = {}
	if file_wordaggs_f0:
		at_header_line = 1
		with open(file_wordaggs_f0, 'rt') as f:
			reader = csv.reader(f, delimiter=' ', quotechar=None)
			for row in reader:
				if at_header_line:
					at_header_line = 0
				else:
					word_id_to_f0_features_dic[row[0]] = featureVectorToFloat(row[6:36])

	#read wordaggs_i0 file to a dictionary
	word_id_to_i0_features_dic = {}
	if file_wordaggs_i0:
		at_header_line = 1
		with open(file_wordaggs_i0, 'rt') as f:
			reader = csv.reader(f, delimiter=' ', quotechar=None)
			for row in reader:
				if at_header_line:
					at_header_line = 0
				else:
					word_id_to_i0_features_dic[row[0]] = featureVectorToFloat(row[6:36])  #acoustic features

	#read aligned word file to a dictionary (word.align)
	word_data_aligned_dic = {}
	if file_wordalign:
		word_data_aligned_dic = OrderedDict()
		with open(file_wordalign, 'rt') as f:
			reader = csv.reader(f, delimiter='\t', quotechar=None)
			first_line = 1
			for row in reader:
				if first_line:
					first_line = 0
					continue
				word_data_aligned_dic[row[7]] = [row[5], row[6], row[9]] #starttime, endtime, word

	#if raw folders are given read files under for f0/i0 contours
	word_id_to_raw_f0_features_dic = {}
	if dir_raw_f0:
		for word_id in word_id_list:
			file_f0_vals = os.path.join(dir_raw_f0, "%s.PitchTier"%word_id)
			word_id_to_raw_f0_features_dic[word_id] = []
			if os.path.exists(file_f0_vals):
				with open(file_f0_vals, 'rt') as f:
					reader = csv.reader(f, delimiter='\t', quotechar=None)
					duration = 1
					for row in reader:
						if len(row) == 1:
							if len(row[0].split()) == 3:	#this row has the duration information
								duration = float(row[0].split()[1])
						elif len(row) == 2:	#only rows with two values carry pitch information. rest is metadata
							time_percentage = int((float(row[0]) / duration) * 100)
							f0_val = [time_percentage, round(float(row[1]), 3)]
							word_id_to_raw_f0_features_dic[word_id].append(f0_val)

	#if raw folders are given read files under for f0/i0 contours
	word_id_to_raw_i0_features_dic = {}
	if dir_raw_i0:
		for word_id in word_id_list:
			file_i0_vals = os.path.join(dir_raw_i0, "%s.IntensityTier"%word_id)
			word_id_to_raw_i0_features_dic[word_id] = []
			if os.path.exists(file_i0_vals):
				with open(file_i0_vals, 'rt') as f:
					reader = csv.reader(f, delimiter='\t', quotechar=None)
					line_type = 0	#0 - meta, 1 - time info, 2 - intensity value
					row_count = 0
					for row in reader:
						row_count += 1
						if line_type == 1:
							time_percentage = int((float(row[0]) / duration) * 100)
							line_type = 2
						elif line_type == 2:
							word_id_to_raw_i0_features_dic[word_id].append( [time_percentage, round(float(row[0]), 3)] )
							line_type = 1
						else:
							if row_count == 5:
								duration = round(float(row[0]), 2)
							elif row_count == 6:
								line_type = 1	

	
	print("=========love=========")

	return [word_id_to_f0_features_dic, word_id_to_i0_features_dic, word_data_aligned_dic, word_id_to_raw_f0_features_dic, word_id_to_raw_i0_features_dic]

#reads word alignment information from textgrid to proscript. 
#punctuation information is filled wrt transcript info in segments
#TODO: make this function work without speaker information
def get_word_alignment_from_textgrid(proscript, word_tier_no=1, remove_textgrid=False):
	#print("proscript: %s"%proscript.id)
	for speaker_id in proscript.speaker_ids:
		textgrid_file = proscript.get_speaker_textgrid_file(speaker_id)
		textgrid = tgio.openTextgrid(textgrid_file)		#word segmented textgrid with three tiers, segment, word, phoneme
		#print(textgrid.tierNameList[word_tier_no])
		textgrid_wordtier = textgrid.tierDict[textgrid.tierNameList[word_tier_no]]
		prev_segment = None
		for segment in proscript.get_speaker_segments(speaker_id):
			#print("(%s-%s)"%(segment.start_time, segment.end_time))
			#print("segment %i :%s"%(segment.id, segment.transcript))
			wordtier_segment = textgrid_wordtier.crop(segment.start_time, segment.end_time, mode='truncated', rebaseToZero=False)  #tier region corresponding to segment interval

			transcript_tokens = segment.transcript.split()
			if not len(wordtier_segment.entryList) == len(transcript_tokens):
				#print('TextGrid, transcript mismatch @segment %i :%s'%(segment.id, segment.transcript))
				pass
			tier_entry_index = 0
			for token in transcript_tokens:
				#print("token: %s"%token)
				if token == '-':
					segment.needs_split_at.append(tier_entry_index)
				elif tier_entry_index < len(wordtier_segment.entryList):
					#print(wordtier_segment.entryList[tier_entry_index])
					word = Word()
					word.start_time = round(wordtier_segment.entryList[tier_entry_index][0], TIME_PRECISION)
					word.end_time = round(wordtier_segment.entryList[tier_entry_index][1], TIME_PRECISION)
					word.duration = round(word.end_time - word.start_time, TIME_PRECISION)

					if segment.get_last_word():
						word.pause_before = round(word.start_time - segment.get_last_word().end_time, TIME_PRECISION)
					elif prev_segment and prev_segment.get_last_word():
						word.pause_before = round(word.start_time - prev_segment.get_last_word().end_time, TIME_PRECISION)
					else:
						word.pause_before = 0.0

					word.word = wordtier_segment.entryList[tier_entry_index][2]
					if word.word == "<unk>":
						word.word = token.lower()

					word_in_token_search_beginning = re.search(r'\w+', token)
					word_in_token_search_end = re.search(r'\w+', token[::-1])
					
					try:
						word.punctuation_before = token[:word_in_token_search_beginning.start()]
						word.punctuation_after = token[::-1][:word_in_token_search_end.start()][::-1]
					except:
						pass

					#print("puncs: |%s| - |%s|"%(word.punctuation_before, word.punctuation_after))

					segment.add_word(word)
					tier_entry_index += 1
					#print("add_word")
					#print("----------------")
			prev_segment = segment
		if remove_textgrid:
			os.remove(textgrid_file)

#calls praat scripts under the package directory. Make sure they're accessible. 
def laic_call(file_id, wavfile, alignfile, working_dir, get_aggs=True):
	if get_aggs:
		command = "%s/laic/extract-prosodic-feats.sh %s %s %s %s"%(os.path.dirname(os.path.realpath(__file__)), file_id, wavfile, alignfile, working_dir)
	else:
		command = "%s/laic/extract-raw-feats.sh %s %s %s %s"%(os.path.dirname(os.path.realpath(__file__)), file_id, wavfile, alignfile, working_dir)
	print(command)
	with open(os.devnull, 'w') as fp:
		p = subprocess.Popen(command.split())
		p.communicate()

def assign_acoustic_feats(proscript, working_dir=None, get_aggs=True):
	if working_dir == None:
		working_dir = tempfile.mkdtemp()
	elif not os.path.exists(working_dir):
		os.makedirs(working_dir)
	
	alignment_file = os.path.join(working_dir, "%s_alignment.csv"%proscript.id)
	proscript_to_alignfile(proscript, alignment_file)

	laic_call(proscript.id, proscript.audio_file, alignment_file, working_dir, get_aggs)

	if get_aggs:
		file_wordaggs_f0 = os.path.join(working_dir, "f0", "%s.aggs.txt"%proscript.id)
		file_wordaggs_i0 = os.path.join(working_dir, "i0", "%s.aggs.txt"%proscript.id)
	dir_raw_f0 = os.path.join(working_dir, "raw-f0")
	dir_raw_i0  = os.path.join(working_dir, "raw-i0")

	word_id_list = proscript.get_word_id_list()

	if get_aggs:
		[word_id_to_f0_features_dic, word_id_to_i0_features_dic, word_data_aligned_dic, word_id_to_raw_f0_features_dic, word_id_to_raw_i0_features_dic] = readTedDataToMemory(word_id_list=word_id_list, file_wordalign=alignment_file, file_wordaggs_f0=file_wordaggs_f0, file_wordaggs_i0=file_wordaggs_i0, dir_raw_f0=dir_raw_f0, dir_raw_i0=dir_raw_i0)
	else:
		[_, _, _, word_id_to_raw_f0_features_dic, word_id_to_raw_i0_features_dic] = readTedDataToMemory(word_id_list=word_id_list, dir_raw_f0=dir_raw_f0, dir_raw_i0=dir_raw_i0)

	for segment in proscript.segment_list:
		for word in segment.word_list:
			word_id = word.id

			#acoustic features
			if get_aggs:
				try:
					word.f0_mean = float(FLOAT_FORMATTING.format(word_id_to_f0_features_dic[word_id][0]))
					word.f0_slope = float(FLOAT_FORMATTING.format(word_id_to_f0_features_dic[word_id][14]))
					word.f0_sd = float(FLOAT_FORMATTING.format(word_id_to_f0_features_dic[word_id][1]))
					word.f0_range = float(FLOAT_FORMATTING.format(float(word_id_to_f0_features_dic[word_id][2]) - float(word_id_to_f0_features_dic[word_id][3])))
				except:
					print("No f0 features for %s"%word_id)
				try:
					word.i0_mean = float(FLOAT_FORMATTING.format(word_id_to_i0_features_dic[word_id][0]))
					word.i0_slope = float(FLOAT_FORMATTING.format(word_id_to_i0_features_dic[word_id][14]))
					word.i0_sd = float(FLOAT_FORMATTING.format(word_id_to_i0_features_dic[word_id][1]))
					word.i0_range = float(FLOAT_FORMATTING.format(float(word_id_to_i0_features_dic[word_id][2]) - float(word_id_to_i0_features_dic[word_id][3])))
				except:
					print("No i0 features for %s"%word_id)

			#contours
			try:
				f0_contour = np.array(word_id_to_raw_f0_features_dic[word_id])  #this is two dimensional
				word.f0_contour_xaxis = f0_contour[:,0].tolist() if f0_contour.size else []
				word.f0_contour = f0_contour[:,1].tolist() if f0_contour.size else []
				interpolated_contour = np.interp(np.arange(100), word.f0_contour_xaxis, word.f0_contour)
				word.f0_contour_evened = interpolated_contour.tolist() if len(interpolated_contour) else [0] * 100  #bunu bin'le
				#word.f0_contour_evened = interpolated_contour[0::CONTOUR_BIN_NO].tolist() if f0_contour.size else [0] * CONTOUR_BIN_NO	#rename contour_bin_no variable
			except:
				print("No f0 contour for %s"%word_id)
			
			try:
				i0_contour = np.array(word_id_to_raw_i0_features_dic[word_id])  #this is two dimensional
				word.i0_contour_xaxis = i0_contour[:,0].tolist() if i0_contour.size else []
				word.i0_contour = i0_contour[:,1].tolist() if i0_contour.size else []
				interpolated_contour = np.interp(np.arange(100), word.i0_contour_xaxis, word.i0_contour)
				word.i0_contour_evened = interpolated_contour.tolist() if len(interpolated_contour) else [0] * 100 #bunu bin'le
				#word.i0_contour_evened = interpolated_contour[0::CONTOUR_BIN_NO].tolist() if i0_contour.size else [0] * CONTOUR_BIN_NO
			except:
				print("No i0 contour for %s"%word_id)
	
	speaker_f0_means = proscript.get_speaker_means("f0_contour")
	print("speaker f0 mean")
	print(speaker_f0_means)
	speaker_i0_means = proscript.get_speaker_means("i0_contour")

	for segment in proscript.segment_list:
		speaker_id = segment.speaker_id
		for word in segment.word_list:
			word.f0_contour_semitones = [to_semitone(f, speaker_f0_means[speaker_id]) for f in word.f0_contour_evened]
			word.i0_contour_semitones = [to_semitone(f, speaker_i0_means[speaker_id]) for f in word.i0_contour_evened]

			if not get_aggs:
				f0_mean = to_semitone(np.mean(word.f0_contour), speaker_f0_means[speaker_id]) if len(word.f0_contour) > 0 else 0.0
				i0_mean = to_semitone(np.mean(word.i0_contour), speaker_i0_means[speaker_id]) if len(word.i0_contour) > 0 else 0.0
				f0_max = to_semitone(max(word.f0_contour), speaker_f0_means[speaker_id]) if len(word.f0_contour) > 0 else 0.0
				f0_min = to_semitone(min(word.f0_contour), speaker_f0_means[speaker_id]) if len(word.f0_contour) > 0 else 0.0
				i0_max = to_semitone(max(word.i0_contour), speaker_i0_means[speaker_id]) if len(word.i0_contour) > 0 else 0.0
				i0_min = to_semitone(min(word.i0_contour), speaker_i0_means[speaker_id]) if len(word.i0_contour) > 0 else 0.0

				word.f0_mean = f0_mean
				word.i0_mean = i0_mean
				word.f0_range = f0_max - f0_min
				word.i0_range = i0_max - i0_min

			#print("-----")
			#print(word.word)
			# print("raw mean")
			# raw_mean=np.mean(word.f0_contour)
			# print(raw_mean)
			# print("interpolated mean")
			# mean = np.mean(word.f0_contour_evened)
			# print(mean)
			# print("semitone mean from calculated semitone contour")
			# print(np.mean(word.f0_contour_semitones))
			# print("semitone mean from calculated interpolated contour")
			# print(to_semitone(mean, speaker_f0_means[speaker_id]))
			# print("semitone mean from raw contour")
			# print(to_semitone(raw_mean, speaker_f0_means[speaker_id]))  #bunu mean'e koy
			# print("semitone mean from R scripts")
			# print(word.f0_mean)


def to_semitone(f,ref):
	return math.log((f/ref), 2) * 12

def featureVectorToFloat(featureVector):
	features_fixed = [0.0] * len(featureVector)
	for ind, val in enumerate(featureVector):
		if val == 'NA':
			features_fixed[ind] = 0.0
		else:
			features_fixed[ind] = float(FLOAT_FORMATTING.format(float(val)))
	return features_fixed

def assign_word_ids(proscript):
	for segment in proscript.segment_list:
		word_no = 1
		for word in segment.word_list:
			word.id = "%s.segment%s.word%d"%(proscript.id, segment.id, word_no)
			#print(word.id)
			word_no += 1

def proscript_to_alignfile(proscript, alignfile_filename):
	column_tags=['conv', 'spk', 'part', 'sid', 'chno', 'starttime', 'endtime', 'word.id', 'wavfile', 'word']
	with open(alignfile_filename, 'w') as f:
		w = csv.writer(f, delimiter="\t")
		w.writerow(column_tags)
		sid = 1
		for segment in proscript.segment_list:
			for word in segment.word_list:
				if word.duration > 0.0:
					chno = proscript.speaker_ids.index(segment.speaker_id) + 1
					row = [proscript.id, segment.speaker_id, segment.speaker_id, sid, chno, word.start_time, word.end_time, word.id, 'NA', word.word]
					w.writerow(row)
					sid += 1

def assign_pos_tags(segment):
	tokens = [word.word for word in segment.word_list]
	pos_data = nltk.pos_tag(tokens)

	for word_idx, word in enumerate(segment.word_list):
		word.pos = pos_data[word_idx][1]

def read_word_from_dict(word_dict):
	w = Word()
	for key in word_dict.keys():
		w.set_value(key, word_dict[key])
	return w

def read_proscript_as_list(filename, delimiter="|"):
	#reads each row as dict. puts them in a list.
	proscript = []

	with open(filename) as f:
		reader = csv.DictReader(f, delimiter=delimiter) # read rows into a dictionary format
		for row in reader: # read a row as {column1: value1, column2: value2,...}
			proscript.append({k:v for (k,v) in row.items()})

	return proscript

def read_proscript_as_dict(filename, delimiter="|"):
	#reads whole csv into one dict
	proscript = defaultdict(list) # each value in each column is appended to a list

	with open(filename) as f:
		reader = csv.DictReader(f, delimiter=delimiter) # read rows into a dictionary format
		for row in reader: # read a row as {column1: value1, column2: value2,...}
			for (k,v) in row.items(): # go over each column name and value 
				if "word" in k or "punctuation" in k or "pos" in k or "id" in k:
					proscript[k].append(v) # append the value into the appropriate list
				elif "contour" in k:
					arr_rep = json.loads(v)
					proscript[k].append(arr_rep)
				else:
					try:
						proscript[k].append(float(v)) # real value
					except ValueError:
						print("ALARM:%s"%v)
						proscript[k].append(0.0)
	return proscript

def get_transcript(element):
	if type(element) == Word:
		return word.word
	if type(element) == Segment:
		transcript = ""
		for word in element.word_list:
			if word.punctuation_before:
				transcript += word.punctuation_before + " "
			if not word.word == END:
				transcript += word.word + " "
			if word.punctuation_after:
				transcript += word.punctuation_after + " "
		return transcript
	if type(element) == Proscript:
		transcript = ""
		for segment in element.segment_list:
			for word in segment.word_list:
				if word.punctuation_before:
					transcript += word.punctuation_before + " "
				if not word.word == END:
					transcript += word.word + " "
				if not word.word == END and word.punctuation_after:
					transcript += word.punctuation_after + " "
		return transcript



