import DiscreteEventSimulation as DES
import numpy as np
import random as rnd
import scipy.stats as stats
from scipy.stats import poisson

#--COMPUTATION OF----------------------------------------------------------------------------------
class Patient(object):
    def __init__(self, cust_type):
        self.ArrivalTime = DES.currSimTime
        self.type = cust_type #inpatient, outpatient, emergency

lambda_office_hours = (21 / 6)/60  # Average 21 calls over 6 office hours (3.5 calls per hour)
lambda_non_office_hours = (6 / 18)/60  # Average 6 calls over 18 non-office hours (1/3 calls per hour)

def Inpatients_arrivalrate(t):
    global baseline_day

    t_current = t - baseline_day  # Calculate time relative to the start of the day

    if t_current < 9 * 60 or t_current >= 15 * 60:
        return lambda_non_office_hours  # Outside office hours
    else:
        # During office hours, use a sine function to model the rate
        morning_peak = (3.5 * np.sin((t_current - 9 * 60) * np.pi / (3 * 60)))/60
        afternoon_peak = (3.5 * np.sin((t_current - 12 * 60) * np.pi / (3 * 60)))/60
        return lambda_office_hours + (morning_peak if t_current < 12 * 60 else afternoon_peak)

def Inpatients_generateCall(currSimTime):
    max_lambda = lambda_office_hours + (3.5/60)  # Max lambda based on the sine function and peak values

    t = currSimTime
    while True:
        u = np.random.uniform(0, 1)
        t += -np.log(u) / max_lambda
        if np.random.uniform(0, 1) < Inpatients_arrivalrate(t) / max_lambda:
            return t

def Inpatients_generateArrival(T):
    return T + np.random.uniform(9, 15)

def Outpatients_generateCall(T):
    expected_val = 23/(24*60)
    interarrival_time = np.random.exponential(scale=1/expected_val)
    return (T + interarrival_time)

def Emergency_generateArrival(T):
    expected_val = 24/(24*60)
    interarrival_time = np.random.exponential(scale=1/expected_val)
    return (T + interarrival_time)

#--EVENTS: call-in-----------------------------------------------------------------------------------------
class CallOutpatient(DES.Event):
    def description(self):
        return 'outpatient call'

    def execute(self):
        global appointment_list, day_of_week, days, office_hours, outpatients
        scheduling()

        outpatients += 1

        if office_hours:
            next_call = Outpatients_generateCall(DES.currSimTime)       # Generate the next call
            DES.insertEvent(CallOutpatient(next_call))                  # insert event of next call

inpatient_waiting = 0
inpatient_request = 0
day_request = 0

class CallInpatient(DES.Event):
    def description(self):
        return 'inpatient Call'

    def execute(self):
        global inpatient_request, inpatient_waiting,day_request, total_day

        if len(waiting_room) <= 3 or inpatient_waiting < 1:
            arrival_time = Inpatients_generateArrival(DES.currSimTime)
        
            DES.insertEvent(ArrivalInpatient(arrival_time))
        else:
            day_request += 1

        next_call = Inpatients_generateCall(DES.currSimTime)
        DES.insertEvent(CallInpatient(next_call))

week_schedule = np.zeros([5, 28])  # schedule is for weekdays (mon, tues, wedn, thu, fri) and slots (8-12 & 12-16)
waiting_list = []  # waiting_list to save outpatients for scheduling on friday.
difference_time = 0

def scheduling():
    global waiting_list, week_schedule, baseline, difference_time, day_indx, day_difference

    times = [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270, 300, 315, 330, 360, 375, 390, 420, 435, 450]
    if day_indx < 4:
        for slot in range(28):
            week_schedule[day_indx, slot] = 1

    slot_found = False
    scheduled_day_indx = None
    for day in range(4):
        if not slot_found:
            index = np.where(week_schedule[day] == 0)[0]
            if index.any():
                week_schedule[day, index[0]] = 1
                schedule_time = baseline + (24 * 60 * day) + times[index[0]]  # monday 08:00 + days + time
                DES.insertEvent(ArrivalOutpatient(schedule_time))
                difference_time += schedule_time - DES.currSimTime 
                slot_found = True
                scheduled_day_indx = day
                
    if not slot_found:
        waiting_list.append(1)
        

    if scheduled_day_indx is not None:
        if day_indx != 4:
            day_difference.append(scheduled_day_indx - day_indx)
        elif day_indx == 4:
            day_difference.append(3 + scheduled_day_indx)


#--EVENTS: arrival-----------------------------------------------------------------------------------------
class ArrivalEmergency(DES.Event):
    def description(self):
        return 'emergency arrival'

    def execute(self):
        global waiting_room
        patient = Patient('emergency')

        waiting_room.insert(0,patient)
        if scan_available >0:
            startScanning()
        next_arrival = Emergency_generateArrival(DES.currSimTime)
        DES.insertEvent(ArrivalEmergency(next_arrival))

class ArrivalOutpatient(DES.Event):
    def description(self):
        return 'outpatient arrival'

    def execute(self):
        global waiting_room, scan_available

        if rnd.random() < 0.84:
            patient = Patient('outpatient')
            waiting_room.insert(0,patient)
            if scan_available > 0:
                startScanning()


class ArrivalInpatient(DES.Event):
    def description(self):
        return 'inpatient arrival'

    def execute(self):
        global waiting_room, inpatient_waiting, total_inpatients, inpatient_not_same_day
        patient = Patient('inpatient')
        total_inpatients += 1
        waiting_room.append(patient)
        inpatient_waiting += 1
        if not office_hours:
            inpatient_not_same_day += 1
        if scan_available > 0:
            startScanning()

scan_made_in=0
scan_made_out=0

def startScanning():
    global scan_available, scanDuration, inpatient_waiting, inpatient_request, scan_made_in
    global total_waiting_time_em, total_waiting_time_in, total_waiting_time_ot, obs_wait_em, obs_wait_ot
    global scan_inside_office_hours, scan_outside_office_hours, total_scans, inpatient_not_same_day
    global scan_made_out, day_request

    if scan_available > 0:
        if office_hours:
            scan_inside_office_hours += 1
        elif office_hours == False and waiting_room[0].type == 'inpatient':
            inpatient_not_same_day += 1
            scan_outside_office_hours +=1
            
        else:
            scan_outside_office_hours +=1

        scanDuration = rnd.uniform(10,19)
        total_scans += 1
        ending_scan = DES.currSimTime + scanDuration
        DES.insertEvent(EndofScan(ending_scan))

        wait = DES.currSimTime - waiting_room[0].ArrivalTime

        if waiting_room[0].type == 'inpatient':
            inpatient_waiting -= 1
            if inpatient_request > 0:
                arrival_time = Inpatients_generateArrival(DES.currSimTime)
                DES.insertEvent(ArrivalInpatient(arrival_time))
                inpatient_request -= 1
            elif day_request > 0:
                arrival_time = Inpatients_generateArrival(DES.currSimTime)
                DES.insertEvent(ArrivalInpatient(arrival_time))
                day_request -= 1
        if waiting_room[0].type == 'outpatient':
            total_waiting_time_ot += wait
            obs_wait_ot += 1
            access_time = DES.currSimTime - waiting_room[0].ArrivalTime
            access_times.append(access_time)

        if waiting_room[0].type == 'emergency':
            total_waiting_time_em += wait
            obs_wait_em += 1
            total_waiting_time_em += wait
            obs_wait_em += 1

        scan_available -= 1
        waiting_room.pop(0)

# EVENTS: office hours-----------------------------------------------------------------------------------------
class OfficeHours(DES.Event):
    def description(self):
        return 'start of office hours'

    def execute(self):
        global office_hours, day_of_week, baseline
        office_hours = True

        if day_of_week == 'Monday':
            baseline = DES.currSimTime  # baseline on monday 08:00

        first_call = Outpatients_generateCall(DES.currSimTime)
        DES.insertEvent(CallOutpatient(first_call))

        if day_of_week == 'Friday':
            self.Time = self.Time + (3 * 24 * 60)
            baseline = baseline + (7 * 24 * 60)
        else:
            self.Time = self.Time + (24 * 60)

        EoO = DES.currSimTime + (8 * 60)
        EndofOffice = OutOfficeHours(EoO)

        DES.insertEvent(EndofOffice)  # schedule end of office (always 8 hours after start)
        DES.insertEvent(self)  # schedule next start of office (next day, or after weekend)

inpatient_not_same_day = 0

class OutOfficeHours(DES.Event):
    def description(self):
        return 'outside of office hours'

    def execute(self):
        global office_hours, week_schedule, waiting_list,day_request,inpatient_request
        office_hours = False
        inpatient_request += day_request
        day_request = 0

        if day_of_week == 'Friday':
            week_schedule = np.zeros([5, 28])  # reset the schedule
            if len(waiting_list) > 0:
                for c in range(len(waiting_list)):  # make appointments for an outpatient not yet scheduled.
                    scheduling()
                waiting_list = []

# EVENTS: scanning-----------------------------------------------------------------------------------------

class EndofScan(DES.Event):
    def description(self):
        return 'end scanning patient'

    def execute(self):
        global scan_available
        scan_available += 1
        if waiting_room:
            startScanning()

class EndofDay(DES.Event):
    def description(self):
        return 'new day'

    def execute(self):
        global day_of_week, day_indx, total_day,baseline_day, day_ut_in, day_ut_out, scan_inside_office_hours
        global scan_outside_office_hours, obs_wait_em, obs_wait_ot, day_of_batch_ut

        day_ut_in.append(scan_inside_office_hours / 8)
        day_ut_out.append(scan_outside_office_hours / 16)

        scan_inside_office_hours = 0
        scan_outside_office_hours = 0
        
        day_of_batch_ut += 1
        total_day += 1
        day_indx += 1

        if day_indx == 7:
            day_indx = 0
        day_of_week = days[day_indx]

        new_day = EndofDay(DES.currSimTime + (24*60))
        baseline_day = DES.currSimTime
        DES.insertEvent(new_day)


#--BATCH MEANS METHOD-----------------------------------------------------------------------------------------
class WarmUp(DES.Event):
    def description(self):
        return 'end of warm-up'

    def execute(self):
        global BatchQueue, average_queue_length, total_queue, prev_time, total_out
        global BatchWait_E, total_waiting_time_em, obs_wait_em, average_waiting_times_E
        global BatchWait_O, total_waiting_time_ot, obs_wait_ot, average_waiting_times_O
        global BatchWait_I, total_waiting_time_in, average_waiting_times_I
        global BatchLength_em, BatchLength_in, BatchLength_ot, inpatient_not_same_day
        global day_ut_out, day_ut_in

        total_waiting_time_em = 0
        total_waiting_time_ot = 0
        total_waiting_time_in = 0

        BatchLength_em = 4*obs_wait_em
        obs_wait_em = 0
        BatchLength_ot = 4*obs_wait_ot
        obs_wait_ot = 0

        total_queue = 0
        total_out = 0
        prev_time = 0

        BatchWait_E = 0
        BatchWait_O = 0
        BatchWait_I = 0
        BatchQueue = 0

        average_waiting_times_E = []
        average_waiting_times_O = []
        average_waiting_times_I = []
        average_queue_length = []

        inpatient_not_same_day = 0
        


def EndBatchWait_E():
    global BatchWait_E, total_waiting_time_em, obs_wait_em, average_waiting_times_E
    if EndofWarmUp == True and obs_wait_em > 0:
        average_waiting_times_E.append(total_waiting_time_em / obs_wait_em)
        total_waiting_time_em = 0
        obs_wait_em = 0
        BatchWait_E += 1

def EndBatchWait_O():
    global obs_wait_ot, total_waiting_time_ot, BatchWait_O
    if EndofWarmUp == True and obs_wait_ot > 0:
        average_waiting_times_O.append(total_waiting_time_ot / obs_wait_ot)
        total_waiting_time_ot = 0
        obs_wait_ot = 0
        BatchWait_O += 1

def EndBatchUtilization():
    global scan_inside_office_hours, scan_outside_office_hours, total_scans, BatchUtilization_inside
    global BatchUtilization_outside, day_ut_in, day_ut_out, day_of_batch_ut
    if EndofWarmUp:
        if total_scans > 0:
            utilization_inside = np.mean(day_ut_in)
            utilization_outside = np.mean(day_ut_out)
            average_utilization_inside.append(utilization_inside)
            average_utilization_outside.append(utilization_outside)
            scan_inside_office_hours = 0
            scan_outside_office_hours = 0
            total_scans = 0
            day_ut_in = []
            day_ut_out = []
            day_of_batch_ut = 0
            BatchUtilization_inside += 1
            BatchUtilization_outside += 1

def EndBatchAccessTimes():
    global day_difference, BatchAccess_times, outpatients
    if EndofWarmUp and len(day_difference) > 0:
        avg_access_time = np.mean(day_difference)
        average_access_times.append(avg_access_time)
        outpatients = 0
        day_difference = []
        BatchAccess_times += 1

def EndBatchWaitOutside():
    global total_out, BatchOutside_wait, obs_wait_out, outpatients
    if EndofWarmUp and (total_out > 0):
        average_outside_wait.append(total_out/BatchLength2)
        total_out = 0
        BatchOutside_wait += 1
        obs_wait_out = 0

def EndBatchSameDayFail():
    global BatchSame_day_fail, total_inpatients, inpatient_not_same_day
    if EndofWarmUp and inpatient_not_same_day > 0:
        percentage_failed = (inpatient_not_same_day/total_inpatients)
        average_same_day_fail.append(percentage_failed)
        inpatient_not_same_day = 0
        total_inpatients = 0
        BatchSame_day_fail += 1
    elif inpatient_not_same_day == 0:
        percentage_failed = 0
        average_same_day_fail.append(percentage_failed)
        total_inpatients = 0
        BatchSame_day_fail += 1


#--SETUP RUN-----------------------------------------------------------------------------------------
global scan_available,scanDuration
scan_available = 2
scanDuration = (10, 19)  # Normal distribution
waiting_room = []

baseline = 0

outpatients = 0
scan_inside_office_hours = 0
scan_outside_office_hours = 0
total_scans = 0
access_times = []

day_difference = []


global EndofWarmUp
EndofWarmUp = False
WarmUpTime = 4*7*24*60  # UNVERIFIED - 4 weeks to reach steady-state?
default_batch = 24
BatchLength_em = default_batch
BatchLength_ot = default_batch
BatchLength2 = 4*WarmUpTime  # RULE-OF-THUMB
totBatch = 100

total_waiting_time_em = 0
total_waiting_time_ot = 0
obs_wait_em = 0
obs_wait_ot = 0
obs_ut_in = 0
obs_ut_out = 0
obs_access = 0
obs_wait_out = 0
obs_day_fail = 0
total_queue = 0
total_out = 0
total_inpatients = 0
prev_time = 0

BatchWait_E = 0
BatchWait_O = 0
BatchQueue = 0

BatchUtilization_inside = 0
BatchUtilization_outside = 0
BatchAccess_times = 0
BatchWait_times_em = 0
BatchWait_times_ot = 0
BatchOutside_wait = 0
BatchSame_day_fail = 0

day_ut_in = []
day_ut_out = []
average_utilization_inside = []
average_utilization_outside = []
average_access_times = []
average_outside_wait = []
average_same_day_fail = []

average_waiting_times_E = []
average_waiting_times_O = []
average_queue_length = []

inpatient_outside = []


office_hours = False
total_day = 1
day_of_batch_ut = 0
day = 0
day_indx = 0
day_of_week = 'Monday'
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
prev_start = 0

def EndCriterium():
    return BatchQueue >= totBatch

def AfterEvent():
    global total_queue, prev_time, EndofWarmUp, prev_start, total_out, obs_wait_out

    #DES.showEventList(GetInput=False)

    interval = DES.currSimTime - prev_time
    if interval != 0:
        total_queue += (len(waiting_room))*interval
        if len(waiting_room) > 3:
            total_out += ((len(waiting_room) - 3)*interval) 
            obs_wait_out += 1
    prev_time = DES.currSimTime

    if DES.currSimTime >= WarmUpTime and not EndofWarmUp:
        DES.insertEvent(WarmUp(DES.currSimTime))
        EndofWarmUp = True
    if obs_wait_em == BatchLength_em and EndofWarmUp:
        EndBatchWait_E()
    if obs_wait_ot == BatchLength_ot and EndofWarmUp:
        EndBatchWait_O()
    if (DES.currSimTime - prev_start) == BatchLength2 and EndofWarmUp:
        EndBatchWaitOutside()
        EndBatchUtilization()
        EndBatchAccessTimes()
        EndBatchSameDayFail()
        prev_start = DES.currSimTime

DES.insertEvent(EndofDay(0)) #insert change of day.
DES.insertEvent(ArrivalEmergency(0))  # have first patient arrive t=0.
DES.insertEvent(CallInpatient(0)) # have first inpatient call .. continue to generate.
DES.insertEvent(OfficeHours(8 * 60))  # start office hours at 8:00, assuming t=0 is 00:00.

DES.runSimulation(StopCriterium=EndCriterium, ExecuteAfterEveryEvent=AfterEvent)

# Compute performance measures
def compute_final_results(average_values):
    final_avg = np.mean(average_values)
    confidence_interval = stats.t.interval(0.95, len(average_values)-1, loc=final_avg, scale=stats.sem(average_values))
    half_width = abs(final_avg - confidence_interval[0])
    relative_precision = abs(-half_width / (half_width - final_avg))
    return final_avg, confidence_interval, relative_precision

# Compute final results for each set of average values
final_avg_wait_E, conf_int_wait_E, rel_prec_wait_E = compute_final_results(average_waiting_times_E)
final_avg_wait_O, conf_int_wait_O, rel_prec_wait_O = compute_final_results(average_waiting_times_O)
final_avg_access_times, conf_access_times, rel_access_times = compute_final_results(average_access_times)
final_avg_outside_wait, conf_outside_wait, rel_outside_wait = compute_final_results(average_outside_wait)
final_avg_ut_outside, conf_ut_outside, rel_ut_outside = compute_final_results(average_utilization_outside)
final_avg_ut_inside, conf_ut_inside, rel_ut_inside = compute_final_results(average_utilization_inside)
final_avg_day_fail, conf_day_fail, rel_day_fail = compute_final_results(average_same_day_fail)

# Printing results
print("=========================================================================================================================================================")
print(f"General Variables\tWarm-Up time: {WarmUpTime} \t\tAverage EndCriterium: {totBatch} Batches")
print("----------------------------------------------------------------------------------------------------------------------------------------------------------")

# Waiting Time Type E
print(f"Waiting Time Type EM\tBatch Number: {BatchWait_E}\t\tBatch Length: {BatchLength_em} observations\n\t\t\tFinal Average: {round(final_avg_wait_E,4)}\t\tConfidence Interval: ({round(conf_int_wait_E[0],4)},{round(conf_int_wait_E[1],4)})\t\tRelative Precision: {rel_prec_wait_E:.2%}")
print("----------------------------------------------------------------------------------------------------------------------------------------------------------")

# Waiting Time Type O
print(f"Waiting Time Type OT\tBatch Number: {BatchWait_O}\t\tBatch Length: {BatchLength_ot} observations\n\t\t\tFinal Average: {round(final_avg_wait_O,4)}\t\tConfidence Interval: ({round(conf_int_wait_O[0],4)},{round(conf_int_wait_O[1],4)})\t\tRelative Precision: {rel_prec_wait_O:.2%}")
print("----------------------------------------------------------------------------------------------------------------------------------------------------------")

# Access Time
print(f"Access Time\t\tBatch Number: {BatchQueue}\t\tBatch Length: {BatchLength2} minutes\n\t\t\tFinal Average: {round(final_avg_access_times,4)}\t\tConfidence Interval: ({round(conf_access_times[0],4)},{round(conf_access_times[1],4)})\t\tRelative Precision: {rel_access_times:.2%}")
print("----------------------------------------------------------------------------------------------------------------------------------------------------------")

# Waiting outside
print(f"Waiting outside\t\tBatch Number: {BatchQueue}\t\tBatch Length: {BatchLength2} minutes\n\t\t\tFinal Average: {round(final_avg_outside_wait,4)}\t\tConfidence Interval: ({round(conf_outside_wait[0],4)},{round(conf_outside_wait[1],4)})\t\tRelative Precision: {rel_outside_wait:.2%}")
print("----------------------------------------------------------------------------------------------------------------------------------------------------------")

# Utilization Outside
print(f"Utilization Outside\t\tBatch Number: {BatchQueue}\t\tBatch Length: {BatchLength2} minutes\n\t\t\tFinal Average: {round(final_avg_ut_outside,4)}\t\tConfidence Interval: ({round(conf_ut_outside[0],4)},{round(conf_ut_outside[1],4)})\t\tRelative Precision: {rel_ut_outside:.2%}")
print("----------------------------------------------------------------------------------------------------------------------------------------------------------")

# Utilization Inside
print(f"Utilization Inside\t\tBatch Number: {BatchQueue}\t\tBatch Length: {BatchLength2} minutes\n\t\t\tFinal Average: {round(final_avg_ut_inside,4)}\t\tConfidence Interval: ({round(conf_ut_inside[0],4)},{round(conf_ut_inside[1],4)})\t\tRelative Precision: {rel_ut_inside:.2%}")
print("----------------------------------------------------------------------------------------------------------------------------------------------------------")

# Day Fail
print(f"Day Fail\t\tBatch Number: {BatchQueue}\t\tBatch Length: {BatchLength2} minutes\n\t\t\tFinal Average: {round(final_avg_day_fail,4)}\t\tConfidence Interval: ({round(conf_day_fail[0],4)},{round(conf_day_fail[1],4)})\t\tRelative Precision: {rel_day_fail:.2%}")
print("=========================================================================================================================================================\n")
