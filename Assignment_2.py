import DiscreteEventSimulation as DES
import numpy as np
import random as rnd
import scipy.stats as stats

#--COMPUTATION OF----------------------------------------------------------------------------------
def generateInterArrivalTime():
    L = 1.1
    arrival = rnd.expovariate(1/L)
    return arrival

def generateServiceTimeType1():
    return 2

def generateServiceTimeType2():
    M = 2
    service = rnd.expovariate(2/M)+rnd.expovariate(2/M)
    return service

#--CUSTOMER/QUEUE----------------------------------------------------------------------------------
class Customer(object):
    def __init__(self, NumCust, cust_type):
        print('--------------------------------Customer--------------------------------------')

        self.ArrivalTime = DES.currSimTime
        self.NumCust = NumCust
        self.type = cust_type
        # print(f"Customer {NumCust} (Type {cust_type}) arrived at time {self.ArrivalTime}")

def insertCustomer(cust):
    global queue1, queue2
    if len(queue1) == 0 and len(queue2) == 0 and not service1 and not service2:
        endCycle()
        startNewCycle()

    if cust.type == 1:  # insert for type 1
        queue1.append(cust)
    elif cust.type == 2:  # insert for type 2
        queue2.append(cust)

def startService(simTime):
    global nextEndService, total_waiting_time1, total_waiting_time2, service1, service2
    print('--------------------------------Start Service--------------------------------------')

    if not service1:  # check if server1 is busy
        if queue1:
            EoS = simTime + generateServiceTimeType1()  # compute end of service time
            wait = simTime - queue1[0].ArrivalTime  # compute waiting time
            # print(f"Customer {queue1[0].NumCust} (Type 1) starts service at time {simTime} with waiting time {wait}. End of service at {EoS}")
            nextEndService = EndService1(EoS)
            service1 = True  # server1 is busy
            DES.insertEvent(nextEndService)
            queue1.pop(0)  # remove customer from queue
            total_waiting_time1 += wait
        elif queue2:
            n = rnd.random()
            if n <= p:
                EoS = simTime + generateServiceTimeType2()
                wait = simTime - queue2[0].ArrivalTime
                # print(f"Customer {queue2[0].NumCust} (Type 2) starts service at time {simTime} with waiting time {wait}. End of service at {EoS}")
                nextEndService = EndService1(EoS)
                service1 = True
                DES.insertEvent(nextEndService)
                queue2.pop(0)
                total_waiting_time1 += wait

    if not service2:  # check if server2 is busy
        if queue2:
            EoS = simTime + generateServiceTimeType2()  # compute end of service time
            wait = simTime - queue2[0].ArrivalTime  # compute waiting time
            # print(f"Customer {queue2[0].NumCust} (Type 2) starts service at time {simTime} with waiting time {wait}. End of service at {EoS}")
            nextEndService = EndService2(EoS)
            service2 = True  # server2 is busy
            DES.insertEvent(nextEndService)
            queue2.pop(0)
            total_waiting_time2 += wait
        elif queue1:
            n = rnd.random()
            if n <= p:
                EoS = simTime + generateServiceTimeType1()
                wait = simTime - queue1[0].ArrivalTime
                # print(f"Customer {queue1[0].NumCust} (Type 1) starts service at time {simTime} with waiting time {wait}. End of service at {EoS}")
                nextEndService = EndService2(EoS)
                service2 = True
                DES.insertEvent(nextEndService)
                queue1.pop(0)
                total_waiting_time2 += wait

#--EVENTS-----------------------------------------------------------------------------------------
class Arrival(DES.Event):
    def description(self):
        return 'arrival'

    def execute(self):
        global NumCust, p_1, CustType2, CustType1
        NumCust += 1
        n = rnd.random()  # random number 0-1
        if n <= p_1:  # decide type
            cust_type = 1
            CustType1 += 1
        else:
            cust_type = 2
            CustType2 += 1

        print('--------------------------------Execute Arrival-------------------------------------')

        insertCustomer(Customer(NumCust, cust_type))  # insert current arrival

        if (len(queue1) == 1 and not service1) or (len(queue2) == 1 and not service2):  # if the inserted customer is first start a service
            startService(DES.currSimTime)

        self.Time = self.Time + generateInterArrivalTime()  # schedule next arrival
        DES.insertEvent(self)  # insert event

class EndService1(DES.Event):
    
    def description(self):
        return 'end service server 1'

    def execute(self):
        print('--------------------------------End Service--------------------------------------')
        global service1, Customers_done
        service1 = False  # keep track if service is busy
        if queue2 or queue1:
            startService(DES.currSimTime)
        Customers_done += 1
        if (not queue1 and not queue2) and (not service1 and not service2):
            print('--------------------------------Stoopid if statement--------------------------------------')
            endCycle()
            
    

class EndService2(DES.Event):
    def description(self):
        return 'end service server 2'

    def execute(self):
        print('--------------------------------End Service--------------------------------------')
        global service2, Customers_done
        service2 = False
        if queue2 or queue1:
            startService(DES.currSimTime)
        Customers_done += 1
        if (not queue1 and not queue2) and (not service1 and not service2):
            print('--------------------------------Stoopid if statement--------------------------------------')
            endCycle()


#--SETUP RUN-----------------------------------------------------------------------------------------
NumCust = 0
CustType1 = 0
CustType2 = 0
Customers_done = 0
p_1 = 0.5
p = 0
service1 = False
service2 = False
queue1 = []
queue2 = []
Cycle = False


# Regenerative statistics
NumCycles = 1
totCycles = 1
total_waiting_time1 = 0
total_waiting_time2 = 0
average_waiting_times1 = []
average_waiting_times2 = []
average_queue_length1 = []
average_queue_length2 = []
prev_time = 0
total_queue1 = 0
total_queue2 = 0
total_time = 0

def endCycle():
    global NumCycles, total_waiting_time1, total_waiting_time2, CustType1, CustType2, total_queue1,total_queue2,total_time, average_waiting_times1, average_waiting_times2
    print('--------------------------------End Cycle--------------------------------------')
    average_waiting_times1.append(total_waiting_time1 / CustType1)
    average_waiting_times2.append(total_waiting_time2/(CustType2))
                
    average_queue_length1.append(total_queue1/total_time)
    average_queue_length2.append(total_queue2/total_time)
        
    # Reset variables
    total_waiting_time1 = 0
    total_waiting_time2 = 0
    CustType1 = 0
    CustType2 = 0
    total_queue1 = 0
    total_queue2 = 0
    total_time = 0
    NumCycles += 1


def startNewCycle():
    global NumCycles, total_waiting_time1, total_waiting_time2, CustType1, CustType2, total_queue1,total_queue2,total_time, average_waiting_times1, average_waiting_times2
    print('--------------------------------Start Cycle--------------------------------------')

        
    


def EndCriterium():
    return NumCycles == totCycles

def AfterEvent():
    global total_time, total_queue1, total_queue2, prev_time

    total_queue1 += len(queue1)
    total_queue2 += len(queue2)

    total_time += DES.currSimTime - prev_time
    prev_time = DES.currSimTime


DES.insertEvent(Arrival(0))
print('first event')
DES.runSimulation(StopCriterium=EndCriterium, ExecuteAfterEveryEvent=AfterEvent)
print('finished run')

startNewCycle()  # To finalize the last cycle


# ---------------------------------------------- Statistics---------------------------------------------

# Compute performance measures
def compute_final_results(average_values):
    final_avg = np.mean(average_values)
    confidence_interval = stats.t.interval(0.95, len(average_values)-1, loc=final_avg, scale=stats.sem(average_values))
    half_width = abs(final_avg - confidence_interval[0])
    relative_precision = abs(-half_width / (half_width - final_avg))
    return final_avg, confidence_interval, relative_precision

# Final results for waiting times and queue lengths
final_avg_wait1, conf_int_wait1, rel_prec_wait1 = compute_final_results(average_waiting_times1)
final_avg_wait2, conf_int_wait2, rel_prec_wait2 = compute_final_results(average_waiting_times2)
final_avg_queue1, conf_int_queue1, rel_prec_queue1 = compute_final_results(average_queue_length1)
final_avg_queue2, conf_int_queue2, rel_prec_queue2 = compute_final_results(average_queue_length2)

print(average_queue_length1)
# Print results
print(f"Waiting Time Type 1 - Final Average: {final_avg_wait1}, Confidence Interval: {conf_int_wait1}, Relative Precision: {rel_prec_wait1:.2%}")
print(f"Waiting Time Type 2 - Final Average: {final_avg_wait2}, Confidence Interval: {conf_int_wait2}, Relative Precision: {rel_prec_wait2:.2%}")
print(f"Queue Length Type 1 - Final Average: {final_avg_queue1}, Confidence Interval: {conf_int_queue1}, Relative Precision: {rel_prec_queue1:.2%}")
print(f"Queue Length Type 2 - Final Average: {final_avg_queue2}, Confidence Interval: {conf_int_queue2}, Relative Precision: {rel_prec_queue2:.2%}")
print("\n----------------------------------------------------------------------------------------------------------------------------------------------------------\n")