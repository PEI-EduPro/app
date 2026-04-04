# How to run the tests
Get an image of the first page of the exams with the written answers (i.e: example.jpeg).

In `app`, run the following command:
```
./test/test_omr.sh path/to/example.jpg 
```

This should appear at the end of the output:
```
{"status":"success"}
```

To access the output results, in `app`, run this command:
```
logs $(docker ps --filter "name=api" -q) --tail 50
```

Something like this should appear:
```
--- Scoring Breakdown ---
Q01: Weight=0.8 | Value=0.80 | Correct=1, Wrong=0 | Score=0.800
Q02: Weight=0.8 | Value=0.80 | Correct=1, Wrong=0 | Score=0.800
Q03: Weight=0.8 | Value=0.80 | Correct=1, Wrong=0 | Score=0.800
Q04: Weight=0.8 | Value=0.80 | Correct=1, Wrong=0 | Score=0.800
Q05: Weight=0.8 | Value=0.80 | Correct=1, Wrong=0 | Score=0.800
Q06: Weight=1.6 | Value=1.60 | Correct=0, Wrong=0 | Score=0.000
Q07: Weight=0.8 | Value=0.80 | Correct=1, Wrong=0 | Score=0.800
Q08: Weight=0.8 | Value=0.80 | Correct=1, Wrong=0 | Score=0.800
Q09: Weight=0.8 | Value=0.80 | Correct=0, Wrong=0 | Score=0.000
Q10: Weight=1.6 | Value=1.60 | Correct=1, Wrong=0 | Score=1.600
Q11: Weight=0.8 | Value=0.80 | Correct=1, Wrong=0 | Score=0.800
Q12: Weight=0.8 | Value=0.80 | Correct=0, Wrong=0 | Score=0.000
Q13: Weight=1.6 | Value=1.60 | Correct=1, Wrong=0 | Score=1.600
Q14: Weight=0.8 | Value=0.80 | Correct=1, Wrong=0 | Score=0.800
Q15: Weight=1.6 | Value=1.60 | Correct=0, Wrong=0 | Score=0.000
Q16: Weight=0.8 | Value=0.80 | Correct=1, Wrong=0 | Score=0.800
Q17: Weight=0.8 | Value=0.80 | Correct=1, Wrong=0 | Score=0.800
Q18: Weight=1.6 | Value=1.60 | Correct=0, Wrong=0 | Score=0.000
Q19: Weight=0.8 | Value=0.80 | Correct=1, Wrong=0 | Score=0.800
Q20: Weight=0.8 | Value=0.80 | Correct=1, Wrong=0 | Score=0.800

✅ FINAL EXAM SCORE: 13.60 / 20.00
      INFO   172.18.0.1:45636 - "POST /api/exams/exam/evaluate HTTP/1.1" 200
2026-04-04 18:00:10,803 INFO sqlalchemy.engine.Engine ROLLBACK
2026-04-04 18:00:10,803 - sqlalchemy.engine.Engine - INFO - ROLLBACK
```

To copy the graded image to your computer Downloads, in `app`, run this command:
```
docker cp $(docker ps --filter "name=api" -q):/tmp/example_omr_correction.jpg ~/Downloads/
```