import math

def pad(h_or_m,ch):
	s = str(h_or_m)
	if (len(s) < 2):
		s = ch + s 
	return s

def hour_to_time(hour):
	hh = pad(int(math.floor(hour)),' ')
	mm = pad(int((hour - math.floor(hour)) * 60),'0')
	time = hh + ':' + mm
	return time

def plot_spacing(spacingfile,intervals,spacing_0,worstspacing_0,directionname_0,spacing_1,worstspacing_1,directionname_1):

	def plot_spacing_direction(intervals,spacing,worstspacing,directionname):
		sfile.write(directionname + '\n')
		sfile.write('Service period -  Spacing\n')
		for i in range(len(intervals)-1):
			# heuristic: if worst spacing is greater than 1.25 x median spacing, print it also
			if math.isinf(spacing[i]): 
				spacingstr = ''
			else:
				spacingstr = str(int(spacing[i]))
				if float(worstspacing[i]) / float(spacing[i]) > 1.25:
					spacingstr = spacingstr + ' - ' + str(int(worstspacing[i]))
				spacingstr = spacingstr + ' min'
			sfile.write('%s - %s ... %s\n' % (hour_to_time(intervals[i]), hour_to_time(intervals[i+1]), spacingstr))

	sfile = open(spacingfile,'w')
	plot_spacing_direction(intervals,spacing_0,worstspacing_0,directionname_0)
	plot_spacing_direction(intervals,spacing_1,worstspacing_1,directionname_1)
	sfile.close()