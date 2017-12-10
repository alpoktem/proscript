import os
import sys
import csv

END = "<END>"

class Word(object):
	def __init__(self):
		self.id = ""
		self.word = None
		#timing parameters
		self.duration = 0.0				#seconds
		self.end_time = 0.0				#seconds
		self.start_time = 0.0				#seconds
		self.pause_before = 0.0  			#seconds
		self.pause_after = 0.0				#seconds
		#speech rate parameters
		self.speech_rate_phon = -1			
		self.speech_rate_normalized = -1
		#acoustic parameters
		self.f0_contour = -1
		self.i0_contour = -1
		self.f0_contour_xaxis = -1 
		self.i0_contour_xaxis = -1 
		self.f0_mean = 0.0
		self.i0_mean = 0.0
		self.f0_slope = 0.0
		self.i0_slope = 0.0
		self.f0_median = 0.0
		self.i0_median = 0.0
		self.f0_sd = 0.0
		self.i0_sd = 0.0
		self.f0_range = 0.0
		self.i0_range = 0.0
		#linguistic parameters
		self.pos = "NA"
		self.punctuation_before = ""
		self.punctuation_after = ""

	def get_value(self, property_name):
		if hasattr(self, property_name):
			value = getattr(self, property_name)
			return value
		else:
			return None

	def set_value(self, property_name, new_value):
		if hasattr(self, property_name):
			setattr(self, property_name, new_value)

class Segment(object):
	def __init__(self):
		self.start_time = -1.0
		self.end_time = -1.0
		self.transcript = ""
		self.id = ""
		self.speaker_id = ""
		self.word_list = []
		self.word_aligned = False

	def add_word(self, word):
		self.word_list.append(word)

	def get_last_word(self):
		if len(self.word_list) > 0:
			return self.word_list[-1]
		else:
			return None

	def get_no_of_words(self):
		return len(self.word_list)

	def to_string(self):
		#print("segment id: %s"%self.id)
		print("%i (%s): %.2f-%.2f"%(self.id, self.speaker_id, self.start_time, self.end_time))		
		print("transcript: %s"%self.transcript)

	def get_value(self, property_name):
		if hasattr(self, property_name):
			value = getattr(self, property_name)
			return value
		else:
			return None

	def set_value(self, property_name, new_value):
		if hasattr(self, property_name):
			setattr(self, property_name, new_value)

	def get_duration(self):
		#if time values are set:
		duration = self.end_time - self.start_time
		return max(0.0, duration)
		#if not:
		#calculate from last word and first word

	def add_end_token(self):
		end_word = Word()
		end_word.word = END
		self.add_word(end_word)

class Proscript(object):
	def __init__(self):
		self.segment_list = []
		self.features_extracted = False
		#self.word_list = []
		self.word_feature_set = ["start_time", "end_time", "duration", "pause_before", "pause_after", "pos", "punctuation_before", "punctuation_after", "speech_rate_phon", "f0_mean", "i0_mean", "f0_slope", "i0_slope", "f0_sd", "i0_sd", "f0_range", "i0_range", "f0_contour_xaxis", "f0_contour", "i0_contour_xaxis", "i0_contour"]
		self.duration = -1.0
		self.speaker_ids = []
		self.speaker_textgrid_files = [] #textgrid file for each speaker, aligned with self.speaker_ids
		self.textgrid_file = ""
		self.audio_file = ""
		self.id = ""
		self.xml_file = ""

	def get_speaker_textgrid_file(self, speaker_id):
		index = self.speaker_ids.index(speaker_id)
		return self.speaker_textgrid_files[index]

	def add_segment(self, segment):
		self.segment_list.append(segment)
	
	def get_last_segment(self):
		if self.get_no_of_segments() > 0:
			return self.segment_list[-1]
		else:
			return None

	def get_last_word(self):
		if self.get_no_of_segments() > 0:
			return self.get_last_segment().get_last_word()
		else:
			return None

	def get_speaker_segments(self, speaker_id):
		speaker_segments = []
		for segment in self.segment_list:
			if segment.speaker_id == speaker_id:
				speaker_segments.append(segment)
		return speaker_segments

	def get_no_of_segments(self):
		return len(self.segment_list)

	def to_csv(self, csv_filename, word_feature_set=[], segment_feature_set=[], delimiter="|"):
		if not word_feature_set:
			word_feature_set = self.word_feature_set
		with open(csv_filename, 'w') as f:
			w = csv.writer(f, delimiter=delimiter)
			rowIds = ['word'] + segment_feature_set + word_feature_set
			w.writerow(rowIds)
			for segment in self.segment_list:
				for word in segment.word_list:
					row = [word.word]
					row += [segment.get_value(feature_id) for feature_id in segment_feature_set]
					row += [word.get_value(feature_id) for feature_id in word_feature_set]
					w.writerow(row) 

	def segments_to_csv(self, csv_filename, segment_feature_set=[], delimiter="|"):
		with open(csv_filename, 'w') as f:
			w = csv.writer(f, delimiter=delimiter)
			rowIds = segment_feature_set
			w.writerow(rowIds)
			for segment in self.segment_list:
				row = [segment.get_value(feature_id) for feature_id in segment_feature_set]
				w.writerow(row) 
				