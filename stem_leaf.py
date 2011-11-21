from math import floor
from plot_spacing import pad

left_reversed = 0
day_start = 3 # 0 for midnight; 3 = 3 AM start
trim_schedule = 1 # 
time_12_hours = 1 # or 24

def hour_to_12_or_24(h):
	# convert hour number h to hour string e.g. ' 8 PM'
	if time_12_hours:
		hmod = h % 12
		if hmod == 0: hmod = 12
		hstr = pad(hmod,' ') + ' '
		if h < 12: hstr = hstr + 'AM'
		else: hstr = hstr + 'PM'
	else:
		hstr = pad(h,' ') 
	return hstr

def stem_leaf_tuple(data,modulo):
	tuples = []
	for d in sorted(data):
		d = int(floor(d / 60.)) # first round to minutes
		stm, lf = divmod(d,modulo)
		stm = stm % 24 # wrap hours
		tuples.append( (int(stm), int(lf)) )
	return tuples

def stem_leaf_write_to_file(leftstrs,rightstrs,schedule_to_write,headsign_0,headsign_1,leftlens,stemleaffile):
	maxleftlen = max(leftlens)

	sfile = open(stemleaffile,'w')
	sfile.write(' '*(maxleftlen - len(headsign_0)) + headsign_0 + ' '*8 + headsign_1 + '\n')
	for i in schedule_to_write:
		hh = hour_to_12_or_24(i)				
		sfile.write(' '*(maxleftlen - leftlens[i]) + leftstrs[i] + '|' + hh + '|' + rightstrs[i] + '\n')
	sfile.close()
	
def stem_leaf_write_to_html(leftstrs,rightstrs,schedule_to_write,headsign_0,headsign_1,stemleaffile):
	sfile = open(stemleaffile,'w')
	sfile.write('<HTML><HEAD><TITLE>' + stemleaffile + '</TITLE>')

	# write CSS
	sfile.write('<STYLE type="text/css"> table { margin: 1em; border-collapse: collapse; } td, th { padding: .3em; border: 1px #ccc solid; } thead { background: #fc9; } </STYLE>')

	sfile.write('</HEAD><BODY>')
	
	# write table
	sfile.write('<table><thead><tr><th>' + headsign_0 + '</th><th></th><th>' + headsign_1 + '</th></tr></thead><tbody>')
	for i in schedule_to_write:
		hh = hour_to_12_or_24(i)				
		sfile.write('<tr><td align="right">' + leftstrs[i] + '</td><td align="right">' + hh + '</td><td>' + rightstrs[i] + '</td></tr>')
	sfile.write('</tbody></table>')
	
	sfile.write('</BODY></HTML>')
	sfile.close()


def stem_leaf_schedule(timelist_0, headsign_0, timelist_1 = [], headsign_1 = '', stemleaffile = ''):
		
	# init some structures
	left_leaf = []
	right_leaf = []
	leftstrs = []
	rightstrs = []
	for i in range(24):
		left_leaf.append([])
		right_leaf.append([])
		leftstrs.append('')
		rightstrs.append('')
		
	# order is [direction 0, direction 1]
	tuples0 = stem_leaf_tuple(timelist_0,60)
	for (stm,lf) in tuples0:
		left_leaf[stm].append(lf)

	tuples1 = stem_leaf_tuple(timelist_1,60) 	
	for (stm,lf) in tuples1:
		right_leaf[stm].append(lf)

	# make list of strings for each hour
	# this should be easy to output to various formats including HTML
	leftlens = []
	rightlens = []
	for i in range(24):
		for l in left_leaf[i]:
			if left_reversed:
				leftstrs[i] = pad(l,'0') + ' ' + leftstrs[i]
			else:
				leftstrs[i] = leftstrs[i] + pad(l,'0') + ' '
				
		for l in right_leaf[i]:
			rightstrs[i] = rightstrs[i] + ' ' + pad(l,'0') 
		
		leftlens.append(len(leftstrs[i]))
		rightlens.append(len(rightstrs[i]))

	# move schedule up/down relative to day start
	schedule_hours = range(24)
	if day_start != 0:
		schedule_hours = schedule_hours[day_start:] + schedule_hours[:day_start]
	
	# trim start and end of new schedule
	if trim_schedule:
		i = 0
		while leftlens[schedule_hours[i]] == 0 and rightlens[schedule_hours[i]] == 0: 
			i = i + 1
		j = 24-1
		while leftlens[schedule_hours[j]] == 0 and rightlens[schedule_hours[j]] == 0: 
			j = j - 1
		schedule_to_write = schedule_hours[i:j+1]
	else:
		schedule_to_write = schedule_hours
	
	print 'Writing stem-leaf schedule file: ' + stemleaffile + '.txt'
	stem_leaf_write_to_file(leftstrs,rightstrs,schedule_to_write,headsign_0,headsign_1,leftlens,stemleaffile + '.txt')

	print 'Writing stem-leaf schedule file: ' + stemleaffile + '.html'
	stem_leaf_write_to_html(leftstrs,rightstrs,schedule_to_write,headsign_0,headsign_1,stemleaffile + '.html')
