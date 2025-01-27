import DiscreteEventSimulation as DES
import numpy as np

#--COMPUTATION OF----------------------------------------------------------------------------------
def arrivalTime():
    if NumCust == 1:
        arrival = 0
    else:
        arrival = 20*(1+np.sin(NumCust*np.pi**2))
    return arrival

def serviceTime():
    return 10*(2+np.cos(NumCust*np.exp(1)))

#--CUSTOMER QUEUE----------------------------------------------------------------------------------
class Customer(object):
    def __init__(self,arrival):
        self.ServiceTime = serviceTime()
        self.ArrivalTime = arrival

def insertCustomer(cust):
    global queue

    if len(queue) < 1:
        queue = [cust]
    else:
        queue.append(cust)

def startService(simTime):
    global nextEndService, customers_over_10_min, total_waiting_time
    if simTime < queue[0].ArrivalTime:
        simTime = queue[0].ArrivalTime

    EoS = simTime + queue[0].ServiceTime #start service + servicetime
    wait = simTime - queue[0].ArrivalTime #start service - arrival
    nextEndService = EndService(EoS)
    DES.insertEvent(nextEndService)

    if wait > 10:
        customers_over_10_min += 1
    total_waiting_time += wait

#--EVENTS-----------------------------------------------------------------------------------------
class Arrival(DES.Event):
    def description(self):
        return 'arrival'

    def execute(self):
        global NumCust, stopSimulation,NumQ
        NumCust += 1

        self.Time = self.Time + arrivalTime()
        insertCustomer(Customer(self.Time))

        if (len(queue)-1) == 0:
            startService(DES.currSimTime)

        DES.insertEvent(self)

        queue_length_over_time[0] += (len(queue)-2)
        queue_length_over_time[1] += 1

class EndService(DES.Event):
    def description(self):
        return 'end service'

    def execute(self):
        queue.pop(0)

        if (len(queue)) != 0:
            startService(DES.currSimTime)

        queue_length_over_time[1] += 1
        queue_length_over_time[0] += (len(queue)-2)

#--SETUP RUN-----------------------------------------------------------------------------------------
NumCust = 0
LastCust = 1000
queue = []
total_waiting_time = 0
customers_over_10_min = 0
queue_length_over_time = [0,0]

def EndCriterium():
    return NumCust >= LastCust

def AfterEvent():
    pass

DES.insertEvent(Arrival(0))
DES.runSimulation(StopCriterium=EndCriterium,ExecuteAfterEveryEvent=AfterEvent)

average_queue = queue_length_over_time[0] / queue_length_over_time[1]
average_waiting_time = total_waiting_time / NumCust
fraction_over_10_min = customers_over_10_min / (NumCust)

print("Average Queue:", average_queue)
print("Average Waiting Time:", average_waiting_time)
print("Fraction of customers waiting more than 10 minutes:", fraction_over_10_min)
#===================================================================================================