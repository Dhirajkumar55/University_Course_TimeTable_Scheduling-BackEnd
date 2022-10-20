% Use this editor as a MiniZinc scratch book
include "globals.mzn";
include "alldifferent.mzn";
int:days;
int:slots;

set of int: daysPerWeek = 1..days;
set of int: slotsPerDay = 1..slots;

set of int: properties = 1..3; 
%property0 = teacher
%property1 = section1
%property2 = section2

int: courses;
int: rooms;
int: sections;
int: teachers;

set of int: sectionList = 1..sections;
set of int: teacherList = 1..teachers;
set of int: roomList = 1..rooms;
set of int: courseList = 1..courses;
set of int: courseIndex = 0..courses;

array[courseList,properties] of int: courseDetails;
array[teacherList,daysPerWeek,slotsPerDay] of 0..1: teacherBusy;
array[courseList] of int: courseCredits;

array[teacherList,daysPerWeek,slotsPerDay] of var courseIndex: teacherRoutine;
array[sectionList,daysPerWeek,slotsPerDay] of var courseIndex: sectionRoutine;
%array[roomList,daysPerWeek,slotsPerDay] of var courseIndex: roomRoutine;

% room-availability constraint
% (tested)
constraint 
forall(d in daysPerWeek,s in slotsPerDay)
    (
           sum(t in teacherList)
           (if teacherRoutine[t,d,s]!=0 
               then 1 
               else 0 
           endif) <= rooms
    );


% Only assigned sections can attend a class. And a section can attend a class only once in a given day
% (tested)
constraint 
forall(i in courseList,sec in sectionList)
    (if courseDetails[i,2] != sec /\
        courseDetails[i,3] != sec
        then forall(d in daysPerWeek,s in slotsPerDay)
           (sectionRoutine[sec,d,s] != i) 
        else 
          forall(d in daysPerWeek)
            (sum(s in slotsPerDay)
               (if sectionRoutine[sec,d,s] == i 
                   then 1 
                   else 0 
               endif) <= 1)
    endif);


% only assigned teachers will conduct a class and same class will not be repeated in the same day
% (tested)
constraint 
forall(i in courseList,t in teacherList)
    (if courseDetails[i,1] != t
      then forall(d in daysPerWeek,s in slotsPerDay)
        (teacherRoutine[t,d,s] != i) 
      else forall(d in daysPerWeek)
        (sum(s in slotsPerDay)
        (if teacherRoutine[courseDetails[i,1],d,s] == i 
            then 1 
            else 0 
        endif) <= 1)
    endif);


% total hours of each course will be equal to credits
% (tested)
constraint 
forall(i in courseList)
    (sum(d in daysPerWeek,s in slotsPerDay)
    (if teacherRoutine[courseDetails[i,1],d,s] == i 
        then 1 
        else 0 
    endif) == courseCredits[i]
    );


% matching teachers' routine with students'
% (tested)
constraint 
forall(t in teacherList,d in daysPerWeek, s in slotsPerDay)
    (if teacherRoutine[t,d,s] > 0
      then 
        sectionRoutine[courseDetails[teacherRoutine[t,d,s],2],d,s] 
            == teacherRoutine[t,d,s] 
        /\ 
        sectionRoutine[courseDetails[teacherRoutine[t,d,s],3],d,s] 
            == teacherRoutine[t,d,s]
      else true 
    endif);


% matching students' routine with teachers'
% (tested)
constraint 
forall(sec in sectionList,d in daysPerWeek, s in slotsPerDay)
    (if sectionRoutine[sec,d,s] > 0
      then teacherRoutine[courseDetails[sectionRoutine[sec,d,s],1],d,s] 
          == sectionRoutine[sec,d,s]
      else true 
    endif
    );


% considering teacher's availability
% (tested)
constraint
forall(t in teacherList, d in daysPerWeek, s in slotsPerDay)
    (
        if teacherBusy[t,d,s] == 1
        then teacherRoutine[t,d,s] = 0
        else true
        endif
    );

