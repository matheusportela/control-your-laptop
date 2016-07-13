import matplotlib.pylab as plt
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
    plt.plot(time, values)
    plt.xlim([0, max(time) + 10])
    plt.ylim([-0.1, 1.1])
    plt.show()
