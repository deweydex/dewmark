---
dewmark: 1
code: dewmark-specimen
version: 1
kind: practice
title: Specimen Paper
module: Specimen paper for the exam format
institution: Dublin and Dún Laoghaire ETB
college: Dublin College Dundrum
session: 2026–2027
total marks: 96
time allowed: 2 hours 30 minutes
timer: shown
calculator: scientific
maths input: text, visual, photo
python from: this file
python reference: yes
show answers: after finishing
practice tests: after finishing
hand in: Keep your PDF and answer file. In the real exam you will upload both to Moodle.
---

## Instructions to candidates

1. Answer Section A, **two** questions from Section B, Section C and Section D.
2. Your work saves as you go.

# Section A: Programming (17 marks)

## Question 1: Functions (17 marks)

### 1(a): Parts of a function (6 marks)

Study the following function. For each term below, give its name or value in this function, and explain what the term means.

```python
def shout_first_word(sentence: str) -> str:
    words = sentence.split()
    first = words[0]
    return first.upper() + "!"

print(shout_first_word("hello there friend"))
```

```boxes
Function name
Parameter(s)
Variable declaration(s)
Return statement
Function call
What would happen if the last line (the function call) were removed?
```

### 1(b): Writing functions (9 marks)

Write the following functions with clear comments, and write tests to show that each works.

#### (i) Longer word (4 marks)

Write a function named `longer_word` that takes two strings and returns whichever is longer. If both have the same length, it returns the first.

```python exec 1(b)(i): your function
# Write your function here
```

```python exec 1(b)(i): your tests
# Call your function and write your tests here
```

#### (ii) Counting a letter (5 marks)

Write a function named `count_letter` with two arguments, `text` and `letter`. It must use a loop to count how many times `letter` appears in `text`. Do not use `.count()`.

```python exec 1(b)(ii): your function
# Write your function here
```

```python exec 1(b)(ii): your tests
# Call your function and write your tests here
```

### 1(c): Reading a loop (2 marks)

Which of these prints the numbers 1 to 5, one on each line?

````choice
A. `for n in range(5): print(n)`
B. `for n in range(1, 6): print(n)`
C.
   ```python
   n = 1
   while n < 5:
       print(n)
       n = n + 1
   ```
D. `print(range(1, 6))`
````

```python exec Question 1: rough work (not marked)
```

# Section B: Answer any two of Questions 2 to 4 (20 marks)

Each question in this section is worth 10 marks. Show your working.

## Question 2: A ladder (10 marks)

A ladder 5.2 m long leans against a vertical wall. Its foot is 1.8 m from the wall, on level ground.

### 2(a): Height (6 marks)

How far up the wall does the ladder reach? Give your answer in metres, correct to two decimal places.

```maths 2(a): working
```

```boxes 2(a): answer
Height = ____ m
```

### 2(b): Angle (4 marks)

Find the angle between the ladder and the ground, correct to the nearest degree.

```maths 2(b): working
```

```boxes 2(b): answer
Angle = ____ °
```

## Question 3: A quadratic (10 marks)

### 3(a): Factorising (4 marks)

Factorise $x^2 - 2x - 8$.

```maths
```

### 3(b): Solving (6 marks)

Hence solve $x^2 - 2x - 8 = 0$.

```maths 3(b): working (input: text, photo)
```

```boxes 3(b): answer
x = ____
x = ____
```

## Question 4: Cards (10 marks)

A card is drawn at random from a standard deck of 52. Find the probability that it is a heart or a king, as a fraction in its lowest terms.

```on-paper 4: working
Show your working on the answer sheet headed "Question 4".
```

```boxes 4: answer
P(heart or king) = ____
```

# Section C: Biology (19 marks)

## Question 5: Enzymes and cells (19 marks)

A student timed how long amylase took to break down starch at different temperatures.

| Temperature (°C) | 10 | 20 | 30 | 40 | 50 | 60 |
| --- | --- | --- | --- | --- | --- | --- |
| Time taken (minutes) | 14 | 8 | 4 | 2 | 5 | did not finish |

### 5(a): Reading the table (2 marks)

At which temperature did the amylase work fastest?

```boxes
Temperature = ____ °C
```

### 5(b): Rate (3 marks)

The rate of the reaction is 1 ÷ time taken. Work out the rate at 40 °C, to two decimal places, and give its unit.

```boxes
Rate = ____
```

### 5(c): The result at 60 °C (4 marks)

Explain why no result was recorded at 60 °C.

```answer
```

```material Figure 1
![A plant cell with three numbered pointers. Pointer 1 points to the thick outer boundary. Pointer 2 points to one of several small oval bodies near the edge. Pointer 3 points to the large pale space in the middle of the cell.](pictures/plant-cell-3.svg)
```

### 5(d): Parts of a cell (3 marks)

Name the parts labelled 1 to 3 in Figure 1.

```boxes
1 ____
2 ____
3 ____
Choose from: cell wall / cell membrane / nucleus / chloroplast / vacuole / mitochondrion
```

### 5(e): Where it happens (4 marks)

Complete each sentence. Use Figure 1 to help you.

```blanks
Photosynthesis takes place in the [chloroplast / nucleus / vacuole].
The cell wall is made mostly of ____.
```

### 5(f): What each part does (3 marks)

Match each part of a cell to its job. One job is not used.

```match
1. Mitochondrion
2. Ribosome
3. Chloroplast

A. Makes proteins
B. Releases energy in respiration
C. Absorbs light for photosynthesis
D. Controls what enters and leaves the cell
```

# Section D: Essay (40 marks)

## Question 6: Recording lectures (40 marks)

"Every lecture should be recorded." Discuss.

Use the planning box first if it helps. It is handed in but carries no marks.

```answer 6: plan (not marked)
```

```essay (about 800 words)
```

# Marking scheme

## Question 1

Topic: functions
Outcomes: 7, 8

### 1(a)

Answers:
1. shout_first_word
2. sentence
3. words, first
4. return first.upper() + "!"
5. shout_first_word("hello there friend")
6. Nothing is printed: the function is defined but never run.

- 1 mark: function name, with what a function name is
- 1 mark: parameter, with what a parameter is
- 1 mark: both variables, with what a declaration is
- 1 mark: the return statement, with what it does
- 1 mark: the call, with what a call does
- 1 mark: nothing is printed, because the function never runs

### 1(b)(i)

```python
def longer_word(first, second):
    # Return the longer string; on a tie, return the first one
    if len(second) > len(first):
        return second
    return first
```

```tests
longer_word("cat", "horse") == "horse"
longer_word("horse", "cat") == "horse"
longer_word("dog", "cat") == "dog"
```

- 2 marks: a working function with the right name and two parameters
- 1 mark: a tie returns the first string
- 1 mark: at least two tests that call the function

### 1(b)(ii) (draft)

```tests
count_letter("banana", "a") == 3
count_letter("", "a") == 0
```

- 2 marks: a loop that visits every character
- 1 mark: the count is returned, not printed
- 1 mark: `.count()` is not used
- 1 mark: at least two tests, including one where the letter is absent

### 1(c)

Answer: B (range(1, 6))

### 2(a)

Answer: 4.88 ± 0.01 m

Model answer: $h = \sqrt{5.2^2 - 1.8^2} = \sqrt{23.8} = 4.878\ldots \approx 4.88$ m

- 3 marks: Pythagoras with the ladder as the hypotenuse
- 2 marks: correct working to 4.878
- 1 mark: 4.88 with the unit

### 2(b)

Answer: 70 ± 1 °

- 2 marks: $\cos\theta = 1.8 / 5.2$, or an equivalent ratio using 2(a)'s answer
- 1 mark: 69.7° before rounding
- 1 mark: 70°

Follow through from the student's own answer to 2(a).

### 3(a)

Answer: (x - 4)(x + 2) / (x + 2)(x - 4)

An expanded answer earns no marks.

### 3(b)

Answers (any order):
1. 4
2. -2

- 2 marks: each factor set equal to zero
- 2 marks: x = 4
- 2 marks: x = -2

### 4

Answer: 4/13

- 2 marks: 13 hearts and 4 kings
- 3 marks: the king of hearts counted once, giving 16 cards
- 3 marks: 16/52
- 2 marks: 4/13 in lowest terms

## Question 5

Topic: enzymes; cell structure
Outcomes: 2, 4

### 5(a)

Answer: 40

### 5(b)

Answer: 0.50 ± 0.005 per minute (2 d.p.)

- 2 marks: 1 ÷ 2 = 0.50
- 1 mark: the unit, per minute or /min

### 5(c)

- 2 marks: the enzyme is denatured at 60 °C
- 1 mark: its active site has changed shape
- 1 mark: so starch no longer fits the active site
- 1 mark: a correct link to the fastest result at 40 °C

### 5(d)

Answers:
1. cell wall
2. chloroplast
3. vacuole / large vacuole / permanent vacuole

Do not accept "cell membrane" for 1.

### 5(e)

Answers:
1. chloroplast
2. cellulose

- 2 marks: chloroplast
- 2 marks: cellulose

### 5(f)

Answer: 1 B, 2 A, 3 C

### 6

- **Argument and structure** (15 marks)
  - 13 to 15: one position, sustained; each paragraph advances it
  - 8 to 12: a clear position, developed unevenly
  - 4 to 7: drifts between positions or retells the title
  - 0 to 3: no discernible argument
- **Evidence and examples** (15 marks)
  - 13 to 15: specific named cases, examined rather than cited
  - 8 to 12: real examples, summarised rather than used
  - 4 to 7: generalities standing in for examples
  - 0 to 3: little or no evidence
- **Clarity and control of language** (10 marks)
  - 8 to 10: precise, controlled prose throughout
  - 4 to 7: clear overall, with lapses
  - 0 to 3: meaning is often unclear
