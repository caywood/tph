import math

def pad(h_or_m,ch):
	# pad an hour or minute value to two characters, with a '0' or a space.
	s = str(h_or_m)
	if (len(s) < 2):
		s = ch + s 
	return s

def hour_to_time(hour):
	# convert hour value (floating point) to hh:mm time (padded to exactly 5 characters)
	hh = pad(int(math.floor(hour)),' ')
	mm = pad(int((hour - math.floor(hour)) * 60),'0')
	time = hh + ':' + mm
	return time

def plot_spacing_direction(sfile,intervals,spacing,worstspacing,directionname):
	# write out the interval spacing table for one direction on route
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


def plot_spacing(spacingfile,intervals,spacing_0,worstspacing_0,directionname_0,spacing_1,worstspacing_1,directionname_1):
	# write to file the spacing table for both directions on route
		
	print 'Writing spacing file: ' + spacingfile
	sfile = open(spacingfile,'w')
	plot_spacing_direction(sfile,intervals,spacing_0,worstspacing_0,directionname_0)
	plot_spacing_direction(sfile,intervals,spacing_1,worstspacing_1,directionname_1)
	sfile.close()
	