# Context

Exam generation is fully working.

Now, we need to be able to correct them.

Before having the OCR, we need to provide the user (professor) with a flow for associating the students to exams.

The solution we though of was the following:

The regent of a subject creates a waiting room connected to a exam config (a batch of generated exams) and he could then assign the professors to be vigilantes.

The idea is that a waiting room has 4 stages:
 - preparation (not iniciated)
 - running
 - closed
 - finished

These 3 stages represent the stages of the flow of the delivery of an exam.

The preparation phase is when the exam has not iniciated, this allows the regent to prepare the waiting rooms in advance, instead of having to do it right before the exam.

The regent iniciates the waiting_room, changing it's state to running.

The running phase is the stage where the vigilante professors (and the regent) can associate a student to an exam. When this happens, a string with "exam_id:student_nmec" needs to be saved into a list stored in the waiting_room. Any professor can associate a student to any exam, even if one of the 2 has already been associated (in theory, each student can only be connected to one exam, and vice-versa). This is because we don't want to stop the workflow by raising errors, these will be handled by the regent once the exam ends.

Once the vigilantes have finished with their work (since students can miss the exam, it might not be mandatory for all students to be associated to all exams), the regent closes the waiting_room. The backend needs to compare all entries of the list and raise errors if they appear.

If there are no errors, or the regent fixed them, all entries on the list need to be mapped to the exams model (it has an optional nmec, the student's nmec is inserted there)

The difference between the stage closed and finished is simple. When the regent closes the waiting room, it goes to the closed state, if there are no errors, it skips directly to the finished state and the associations are made automatically. If there are errors, the waiting room stays in the closed state until the regent clears the errors, when it finally goes to the finished state.

Also, the student list is stored in the exam_config

# Tasks

 - make sure that the waiting room creation endpoint starts the waiting rooms in the preparation state

 - make an endpoint for the regent to start the waiting room (the exam starts)

 - make an endpoint for vigilantes (and the regent) to get all the information regarding the exam they will be overseeing. This includes the student list, state of the waiting room, students list (so it's easier to associate the students to the exams), exam list (ids of all the exams). Also, have fields for stats like total amount of exams, total amount of students and that kind of stuff

 - alter the endpoint student_to_exam to instead add an entry to the waiting room list

 - add an endpoint for the vigilantes (and regent) to request every like 5 seconds or something, where it asks for the number of associated exams, and the number of associated students. Just a metric to help the professors during the time for them to oversee the exam.

 - make an endpoint to close a room. It needs to check if there are problems, for example a student with multiple exams, or an exam with multiple students. If there are errors, raise an error and stop (in this case, just stop, since I don't know yet how to raise and solve those errors). If there are no errors, make the associations and put the waiting room in the finished state.

# On hold
I still do not know how to raise errors when the waiting room closes and how to solve them, so this will be on hold.


# Good practices
Do not make all the logic in the router. Create services and that kind of thing, so it's not to clustered and it remains decoupled. For example, in the endpoint to close a waiting room, make a service to make the connections between the exams and the students, since that will eventually be used after the regent solves the issues in the future.