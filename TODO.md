# Context

Currently, when we close a waiting room, we try to make all the associations between the professors and the students. If there is no problem, we're good and the waiting room finishes. If not, we "generate warnings" (not working yet) and then we stop in the closed state.

With that said we don't like the current way the flow works. I believe that the final state "finished" is useless. So when the closed endpoint is called in a waiting room, we change the state to closed and we make the associations. If there are errors (multiple students to exam or multiple exams to student), we raise warnings (and the associations in relation to those errors are not made). However, all other associations are made correctly.

Possible warnings:
- multiple students to exam
- multiple exams to student
- exam corrected with no student (this is for the future when we start automatic corrections with fotos on exams that do not have students associated with them)

# Tasks

- Update the close waiting room endpoit with the new logic.