from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import numpy as np
import pandas as pd
from minizinc import Instance, Model, Solver
import time
from django.views.decorators.csrf import csrf_exempt
import json


def transform3D(data):
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


def transform2D(data):
    x = len(data)
    y = len(data[0])
    
    transformedData = [[0 for j in range(x)] for i in range(y)] 

    for i in range(x):
        for j in range(y):
            transformedData[j][i] = data[i][j]

    return transformedData


# Create your views here.
@csrf_exempt 
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
    print(courseDetails)
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
        teacherRoutine = transform3D(teacherRoutine)
        sectionRoutine = newData["sectionRoutine"]
        sectionRoutine = transform3D(sectionRoutine)
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
        "TeacherRoutine" : teacherRoutine,
        "SectionRoutine" : sectionRoutine,
        "RoomRoutine" : roomRoutine,
        "TimeTaken" : end - start
    }

    return HttpResponse(JsonResponse(responseData))

@csrf_exempt 
def csvInputSolution(request):

    if(request.method == 'POST'):
        print("It's a post method")

        data = json.loads(request.body.decode("utf-8"))
        #print(data["teacherList"])

        teacherList = data["teacherList"]
        print(len(teacherList))
        courseList = data["courseList"]
        sectionList = data["sectionList"]
        courseDetailsList = data["courseDetailsList"]


        teachers = len(teacherList)
        sections = len(sectionList)
        courses = len(courseList)
        rooms = data["rooms"]
        days = 5
        slots = 6

        print("Teachers: " , teachers)
        print("Sections: ", sections)
        print("Courses: ", courses)
        print("Rooms: ", rooms)
        
        sectionArray = []
        for i in range(sections):
            sectionArray.append(sectionList[i]["name"])

        courseCredits = []
        for i in range(len(courseList)):
            courseCredits.append(courseList[i]["courseCredits"])

        print("CourseCredits: ", courseCredits)

        teacherBusy = []
        teacherArray = []
        for i in range(len(teacherList)): 
            teacherArray.append(teacherList[i]["teacherName"])
            teacherBusy.append(transform2D(teacherList[i]["teacherBusy"]))

        print("TeacherBusy: " ,teacherBusy)

        courseDetails = []
        for i in range(len(courseDetailsList)):
            temp = []
            temp.append(teacherArray.index(courseDetailsList[i]["Teacher"])+1)
            temp.append(sectionArray.index(courseDetailsList[i]["Section1"])+1)
            temp.append(sectionArray.index(courseDetailsList[i]["Section2"])+1)
            courseDetails.append(temp)

        print("CourseDetails: ", courseDetails)

        

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
            teacherRoutine = transform3D(teacherRoutine)
            sectionRoutine = newData["sectionRoutine"]
            sectionRoutine = transform3D(sectionRoutine)
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

        teacherSchedule = []

        for i in range(teachers):
            tempArr = teacherRoutine[i]

            x = len(tempArr)
            y = len(tempArr[0])
            for j in range(x):
                for k in range(y):
                    if(tempArr[j][k] == 0):
                        tempArr[j][k] = ''
                    else:
                        tempArr[j][k] = courseList[tempArr[j][k]-1]["courseName"]

            temp = {
                "teacherName": teacherList[i]["teacherName"],
                "teacherRoutine": tempArr
            }

            teacherSchedule.append(temp)

        print("teacherSchedule: ", teacherSchedule)

        sectionSchedule = []

        for i in range(sections):
            tempArr = sectionRoutine[i]

            x = len(tempArr)
            y = len(tempArr[0])
            for j in range(x):
                for k in range(y):
                    if(tempArr[j][k] == 0):
                        tempArr[j][k] = ''
                    else:
                        tempArr[j][k] = courseList[tempArr[j][k]-1]["courseName"]

            temp = {
                "sectionName": sectionArray[i],
                "sectionRoutine": tempArr
            }

            sectionSchedule.append(temp)

        print("sectionSchedule: ", sectionSchedule)


        roomSchedule = []
        rooms = data["rooms"]
        for i in range(rooms):
            tempArr = roomRoutine[i]

            x = len(tempArr)
            y = len(tempArr[0])

            for j in range(x):
                for k in range(y):
                    if(tempArr[j][k] == 0):
                        tempArr[j][k] = ''
                    else:
                        tempArr[j][k] = courseList[tempArr[j][k]-1]["courseName"]

            temp = {
                "roomNumber": i+1,
                "roomRoutine": tempArr
            }

            roomSchedule.append(temp)

        print("roomSchedule: ", roomSchedule)


    responseData = {
        "TeacherRoutine" : teacherSchedule,
        "SectionRoutine" : sectionSchedule,
        "RoomRoutine" : roomSchedule,
        "TimeTaken" : end - start
    }

    # responseData = {
    #     "m":"hi"
    # }    

    return HttpResponse(JsonResponse(responseData))


    # responseData = {
    #     "m":"hi"
    # }      
    
   