#!/usr/bin/python

import random
import colorsys
import yaml
import bisect

#############################################################################

BCOUNT = 3

random.seed(1)

unique_id = 0
global_time = 0
traffic = []
branches = []
branches_by_ident = {}
markers = []

#############################################################################

def randfloat(a, b):
    return a + (b - a) * random.random()

#############################################################################

def get_id():
    global unique_id
    unique_id += 1
    return unique_id

#############################################################################

def join_msgs_by_recv():
    msgs = []
    for b in branches:
        for b2 in [branch for branch in branches if branch.ident != b.ident]:
            for msg in b.sent[b2.ident]:
                msgs.append((msg[1], msg[2], b2))
    msgs.sort()
    return msgs

#############################################################################

def join_events():
    events = []
    for b in branches:
        for b2_ident, msgs in b.sent.items():
            for msg in msgs:
                events.append((msg[0], "S", b.ident, b2_ident, msg[2], msg[3]))
                events.append((msg[1], "R", b2_ident, b.ident, msg[2], msg[3]))
    events.sort()
    return events

#############################################################################

class BankBranch(object):
    def __init__(self, ident):
        self.ident = ident
        self.cash = 100
        self.sent = {} # dst:(ts_send, ts_recv, data, color)

    def send_msg(self, dst, time_send, data, color="#000000"):
        sent = self.sent.setdefault(dst.ident, [])
        if len(sent) == 0:
            idx = 0
        else:
            for idx in range(len(sent)):
                if sent[idx][0] > time_send:
                    break
            else:
                idx += 1 # insert it at the end
        
        d = random.random() * 2

        if len(sent) == 0:
            time_recv = time_send + d
        elif (idx == len(sent)):
            time_recv = max(time_send, sent[idx - 1][1]) + d
        elif (idx == 0):
            time_recv = randfloat(time_send, sent[idx][1])
        else:
            sts = max(time_send, sent[idx - 1][1])
            ets = sts + 2
            time_recv = randfloat(sts, min(ets, sent[idx][1]))
        
        msg = (time_send, time_recv, data, color)
        sent.insert(idx, msg)
        return msg

    def send_money(self, dst, time_send, money):
        self.send_msg(dst, time_send, str(money))

    def send_marker(self, time_send, mid, color):
        for b in [branch for branch in branches if branch.ident != self.ident]:
            tsend, trecv, data, color = self.send_msg(b, time_send, mid, color)

    def initiate_snapshot(self, time_start):
        mid = "M" + str(get_id())
        markers.append(mid)
        hue = random.random()
        color = [("%02x" % int(band * 0xFF))
                  for band in colorsys.hls_to_rgb(hue, 0.4, 1.0)]
        color = "#" + "".join(color)
        self.send_marker(time_start, mid, color)

        received = set([self.ident])
        for i in range(BCOUNT - 1):
            msgs = join_msgs_by_recv()
            for idx, (ts_recv, data, branch) in enumerate(msgs):
                if (data == mid) and (branch.ident not in received):
                    branch.send_marker(ts_recv, mid, color)
                    received.add(branch.ident)
                    break

#############################################################################

# create bank branches
for i in range(BCOUNT):
    bb = BankBranch("SUB%i" % (i + 1))
    branches.append(bb)
    branches_by_ident[bb.ident] = bb

###############

for i in range(30):
    subbranch1 = random.randint(0, BCOUNT - 1)
    subbranch2 = random.randint(0, BCOUNT - 1)
    global_time += random.random() * 1.5
    money = random.randint(5, 20)

    if subbranch1 != subbranch2:
        branches[subbranch1].send_money(branches[subbranch2], global_time, money)

###############

global_time = 0
for i in range(5):
    subbranch = random.randint(0, BCOUNT - 1)
    global_time += randfloat(3, 7)
    branches[subbranch].initiate_snapshot(global_time)

###############

marks = []
for branch in branches:
    marks.append({"p": branch.ident, "ts": 0, "text": str(branch.cash),
                "color":"#787878"})

opened_markers = dict([(b.ident, {}) for b in branches])
for (ts, kind, ident, ident2, data, color) in join_events():
    branch = branches_by_ident[ident]
    if data.startswith("M"):
        if data not in opened_markers[ident]:
            recvs = set()
            if kind == "R":
                recvs.add(ident2)
            marker = [branch.cash, recvs, dict([(b2.ident, 0) for b2 in branches 
                                                if b2.ident != branch.ident])]
            opened_markers[ident][data] = marker
        else:
            marker = opened_markers[ident][data]
            if kind == "R":
                marker[1].add(ident2)
                if len(marker[1]) == BCOUNT - 1:
                      queues = marker[2]
                      transfers = [str(queues[b.ident]) 
                                      for b in branches if b.ident in queues]
                      text = "%i|%s" % (marker[0], ";".join(transfers))
                      marks.append({
                          "p": branch.ident,
                          "ts": ts,
                          "text": text,
                          "color": color
                        })
                    
    else:
        money = int(data)
        if kind == "S":
            money = -money
        branch.cash += money
        marks.append({
            "p": branch.ident, "ts": ts, "text": str(branch.cash), "color": "#787878"
          })

        if kind == "R":
            markers = opened_markers[ident]
            for _, recvs, queues in markers.values():
                if ident2 not in recvs:
                    queues[ident2] += money

###############

traffic = []
for branch in branches:
    for dst in [b.ident for b in branches]:
        if dst == branch.ident:
            continue
        for ts_send, ts_recv, data, color in branch.sent[dst]:
            traffic.append({
                "src": {
                    "p": branch.ident,
                    "ts": ts_send
                  },
                "dst": {
                    "p": dst,
                    "ts": ts_recv
                  },
                "data": data, "color": color
              })

print yaml.dump({
    "processes": [b.ident for b in branches],
    "traffic": traffic,
    "marks": marks
  })

