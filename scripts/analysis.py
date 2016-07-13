import sys

if len(sys.argv) < 2:
    print 'Usage: plot.py [filename]'
    sys.exit(1)

filename = sys.argv[1]
with open(filename) as f:
    lines = f.readlines()
    data = [l.split() for l in lines]
    time = [int(d[0]) for d in data]
    values = [int(d[1]) for d in data]

#margin = 30
#for i in range(1, len(time)):
#    if 500 - margin < (time[i] - time[i-1]) < 500 + margin:
#        print 0,
#    elif 1600 - margin < (time[i] - time[i-1]) < 1600 + margin:
#        print 1,
#print

ZERO_DURATION = 500
ONE_DURATION = 1600
MARGIN = 50
begin_time = 0
end_time = 0
last_value = 0
for t, v in zip(time, values):
    if last_value == 0 and v == 1:
        begin_time = t
    elif last_value == 1 and v == 0:
        end_time = t
        diff = end_time - begin_time

        if abs(diff - ZERO_DURATION) <= MARGIN:
            print '0,',
        elif abs(diff - ONE_DURATION) <= MARGIN:
            print '1,',

    last_value = v
