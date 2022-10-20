from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import numpy as np
import pandas as pd
from minizinc import Instance, Model, Solver
import time


def transform(data):
    x = len(data)
    y = len(data[0])
    z = len(data[0][0])

    transformedData = [[[0 for k in range(y)] for j in range(z)] for i in range(x)]

    for i in range(x):
        for j in range(z):
            for k in range(y):
                transformedData[i][j][k] = data[i][k][j]

    print(x,y,z)
    return transformedData

# Create your views here.

def solution(request):

    # Parameters
    try:
        source = request[0]
    except:
        source = "./solver/lib/classDetails2.csv"
    
    rooms = 8
    slots = 6
    days = 5


    data = pd.read_csv(source)
#     data = data[0:36]


    courseDetails = data.to_numpy(dtype=int).tolist()
    # print(courseDetails)
    sections1 = max(data["Section1"].to_numpy(dtype=int))
    sections2 = max(data["Section2"].to_numpy(dtype=int))
    sections = max(sections1,sections2)
    teachers = max(data["Teacher"].to_numpy(dtype=int))
    courses = int(len(data))
    print("Teachers: ",teachers)
    print("Sections: ",sections)
    print("Courses: ",courses)
    
    tBusy = np.zeros((teachers,5,6))
    for i in range(0,6):
        tBusy[0,0,i] = 1
        tBusy[0,1,i] = 1
        tBusy[1,0,i] = 1

    teacherBusy = tBusy.astype(int).tolist()
    
    courseCredits = np.ones((courses)) * 3
    courseCredits = courseCredits.astype(int).tolist()

    # Load uctp model from file
    uctp = Model("./solver/lib/uctp_copy.mzn")
    # Find the MiniZinc solver configuration for Gecode
    chuffed = Solver.lookup("chuffed")
    # Create an Instance of the uctp model for Gecode
    instance = Instance(chuffed, uctp)
    # assign the data to the instance for data lookup

    instance["days"] = days
    instance["slots"] = slots
    instance["courses"] = courses
    instance["rooms"] = rooms
    instance["sections"] = sections
    instance["teachers"] = teachers
    instance["courseDetails"] = courseDetails
    instance["teacherBusy"] = teacherBusy
    instance["courseCredits"] = courseCredits

    print("Starting Model")
    start = time.time()
    newData = instance.solve()
    end = time.time()
    # print(newData)
    # print(newData["teacherRoutine"])
    # print(newData["sectionRoutine"])
    print("Total time required to run the model ",end-start, " seconds")


    if len(newData)>0:
        # teacherRoutine = np.array(newData["teacherRoutine"])
        # sectionRoutine = np.array(newData["sectionRoutine"])
        teacherRoutine = newData["teacherRoutine"]
        teacherRoutine = transform(teacherRoutine)
        sectionRoutine = newData["sectionRoutine"]
        sectionRoutine = transform(sectionRoutine)
        print("Teacher Routine: ")
        print(teacherRoutine)
        print()
        print("Section Routine: ")
        print(sectionRoutine)
        print()
    else:
        print(newData)


    roomRoutine = np.zeros((rooms,slots,days),dtype=int)
    totalCourses = 0
    for i in range(slots):
        for j in range(days):
            myRoom = 0
            for k in range(teachers):
                if teacherRoutine[k][i][j] > 0:
                    roomRoutine[myRoom][i][j] = teacherRoutine[k][i][j]
                    myRoom += 1
    for rooms in roomRoutine:
        for day in rooms:
            for slot in day:
                if slot > 0:
                    totalCourses += 1
    print("Room Routine: ")
    roomRoutine = roomRoutine.tolist()
    print(roomRoutine)
    print(totalCourses)

    responseData = {
        "Teacher Routine" : teacherRoutine,
        "Section Routine" : sectionRoutine,
        "Room Routine" : roomRoutine,
        "Time Taken" : end - start
    }

    return HttpResponse(JsonResponse(responseData))

