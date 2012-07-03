#!/usr/bin/python

import random
import colorsys
import bisect
import yaml

def random_cmd():
    if random.random() > 0.7:
        return "%%%i" % random.randint(5, 9)
    else:
        val = random.randint(-5, 5)
        if val == 0: val = 1
        if val > 0:
          return "+" + str(val)
        else:
          return str(val)

def process_cmd(cmd, cash):
    num = float(cmd[1:])
    if cmd[0] == "+":
        cash += num
    elif cmd[0] == "-":
        cash -= num
    else:
        cash *= 1.0 + num / 100.0
    return cash

random.seed(1)

PCOUNT = 3

processes = ["SEQ"]
for i in range(PCOUNT):
    processes.append("P%i" % (i + 1))

traffic = []
t = dict([(i, 0.0) for i in range(PCOUNT)])

seq_recv = []

for i in range(20):
    st = random.random() * 6 + 1.0
    tt = random.random() * 4.0 + 1.0
    src = random.randint(0, PCOUNT - 1)
    t[src] += st
    tsrc = t[src]
    data = random_cmd()
    hue = random.random()
    color = [("%02x" % int(band * 0xFF)) for band in colorsys.hls_to_rgb(hue, 0.4, 1.0)]
    color = "#" + "".join(color)

    seq_recv.append((tsrc + tt, data, color))

    traffic.append({
        "src": {
            "p": "P%i" % (src + 1),
            "ts": tsrc
          },
        "dst": {
            "p": "SEQ",
            "ts": tsrc + tt
          },
        "data": data,
        "color": color
      })

seq_recv.sort(lambda x,y: cmp(x[0], y[0]))
recvs = dict([(i, []) for i in range(PCOUNT)])
for seqnum, (ts, data, color) in enumerate(seq_recv):
    for dst in range(PCOUNT):
        tt = random.random() * 4.0 + 1.0
        traffic.append({
            "src": {
                "p": "SEQ",
                "ts": ts
              },
            "dst": {
                "p": "P%i" % (dst + 1),
                "ts": ts + tt
              },
            "data": "%s;%i" % (data, seqnum),
            "color": color
          })
        recvs[dst].append((ts + tt, data, seqnum))

marks = []
cash = dict([(i, 100.0) for i in range(PCOUNT)])
last_seq = dict([(i, 0) for i in range(PCOUNT)])
for i, c in enumerate(cash.values()):
    marks.append({"p": "P%i" % (i + 1), "ts": 0, "text":"[];%i" % int(c),
                  "color": "#000000"})
for proc in range(PCOUNT):
    precv = recvs[proc]
    precv.sort(lambda x,y: cmp(x[0], y[0]))
    queue = [] # (seqnum, cmd)
    for ts, cmd, seqnum in precv:
        keys = [x[0] for x in queue]
        idx = bisect.bisect_left(keys, seqnum)
        queue.insert(idx, (seqnum, cmd))
        txt = "[%s]" % "|".join([str(x[1]) for x in queue])

        processed = False
        while queue and (last_seq[proc] == queue[0][0]):
            processed = True
            cash[proc] = process_cmd(queue[0][1], cash[proc])
            last_seq[proc] += 1
            del queue[0]
        
        txt += ";%i" % int(cash[proc])
        marks.append({"p": "P%i" % (proc + 1), "ts": ts, "text":txt,
                      "color": "#000000" if processed else "#787878"})


print yaml.dump({"processes": processes, "traffic": traffic, "marks": marks})
