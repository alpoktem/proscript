###########################################################################
#                                                                      	  #
#  Praat Script: PROSODY TAGGER                                     	  #
#  Copyright (C) 2016  Mónica Domínguez-Bajo - Universitat Pompeu Fabra   #
#																		  #
#    This program is free software: you can redistribute it and/or modify #
#    it under the terms of the GNU General Public License as published by #
#    the Free Software Foundation, either version 3 of the License, or    #
#    (at your option) any later version.                                  #
#                                                                         #
#    This program is distributed in the hope that it will be useful,      #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of       #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        #
#    GNU General Public License for more details.                         #
#                                                                         #
#    You should have received a copy of the GNU General Public License    #
#    along with this program.  If not, see http://www.gnu.org/licenses/   #
#                                                                         #
###########################################################################
##### MODULE 4F0 ############################################################
###### F0 annotation	version 20180511								  #
###########################################################################
clearinfo
form Parameters
	text directory
	text basename
endform

Read from file: directory$ + "/" + basename$ + ".TextGrid"
Read from file: directory$ + "/" + basename$ + ".wav"

# Variables for objects in Menu
sound$ = "Sound " + basename$
text$ = "TextGrid " + basename$ 
pitch$ = "Pitch " + basename$
int$ = "Intensity " + basename$

empty$ = ""

# Create Intensity Object
selectObject: sound$
To Intensity: 100, 0, "yes"
# Create Pitch object
selectObject: sound$
To Pitch: 0, 75, 300


selectObject: text$
n_int = Get number of intervals: 2
count_sound = 0
for i from 1 to n_int
	selectObject: text$
	int_label$ = Get label of interval: 2, i
	#appendInfoLine: int_label$
	if int_label$ <> ""
		start = Get starting point: 2, i
		end = Get end point: 2, i
		selectObject: pitch$
		f0_mean = Get mean: start, end, "Hertz"
		f0_mean$ = fixed$ (f0_mean, 0)
		selectObject: int$
		int_mean = Get mean: start, end, "dB"
		int_mean$ = fixed$ (int_mean, 0)
		# Write features
		selectObject: text$
		newlabel$ = int_label$ + "@{f0_mean_hz:" + f0_mean$ + ", i0_mean_db:" + int_mean$ + "}"
		Set interval text: 2, i, newlabel$
	endif
endfor
# Save changes to directory
Write to text file: directory$ + "/" + basename$ + ".TextGrid"

# clean Menu
select all
Remove

appendInfoLine: "Textgrid tagged with Prosody!"
### END OF MODULE 4alp #################
