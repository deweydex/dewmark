---
exam_id: pdp-5n2927-sample
title: Sample Examination
module: Programming and Design Principles 5N2927
session: 2025–2026
institution: Dublin and Dún Laoghaire ETB
college: Dublin College Dundrum
kind: sample
total_marks: 60
duration_minutes: 120
allow_completion: true
show_reference: true
reference_theory: false
time_limit_seconds: 10
error_hints: true
---

# Programming and Design Principles 5N2927: Sample Examination

**Weighting:** 30% of the module (60 marks, divided by 2).  **Time allowed:** 2 hours.

This sample paper has the same structure, question types and marks as the final examination. Use it to get comfortable with the exam tool and to check which topics you need to revise.

## Instructions to candidates

1. Answer all four questions. Each question is worth 15 marks, and the paper is marked out of 60.
2. Write code answers in the code cells. Click **Run**, or press **Ctrl+Enter** (Cmd+Enter on a Mac), to run a cell. Add comments that explain what your code does.
3. Write written answers in the white answer boxes. The boxes grow as you type.
4. When a program asks for input, a small box appears at the top of the screen. Type your answer there and press Enter.
5. If your code runs for longer than 10 seconds, the tool stops it. This usually means that a loop never ends.
6. Your work saves automatically. Press **Save** in the toolbar as well from time to time.
7. The **Python reference** button opens a guide to the Python you have learned. The **Settings** button changes the font, text size, colours and code editor.
8. When you finish, follow the three steps at the end of the paper.

### Learning outcomes assessed

This paper assesses the following learning outcomes of module 5N2927.

- (1) Demonstrate an understanding of the historical development of computer programming.
- (3) Differentiate between programming languages by identifying their distinguishing characteristics.
- (6) Summarise a broad range of structured programming and design concepts to include pseudo-code, storage and control structures (selection and iteration).
- (7) Develop a range of documented computer programs to solve a variety of familiar and unfamiliar specified problems.
- (8) Utilise a selection of modularisation concepts such as functions, procedures, variable scope and parameter passing.

---

## Question 1: Programming Languages and Variables (15 marks)

### 1A: Programming languages (3 marks)

**(i)** Name three high-level programming languages.

```answer 1A (i)
```

**(ii)** Explain the difference between a compiler and an interpreter. Is Python usually compiled or interpreted?

```answer 1A (ii)
```

**(iii)** Put the following in order, from the oldest to the newest: Python, machine code, FORTRAN, assembly language.

```answer 1A (iii)
```

### 1B: Variable names (3 marks)

Which of the following are permitted as variable names in Python? Rewrite each one that is not permitted so that it becomes a permitted name.

(i) `total score`
(ii) `total_score`
(iii) `3rd_place`
(iv) `class`
(v) `_count`
(vi) `price-each`

```answer 1B
Permitted:

Not permitted:

My fixed versions:
```

You can use this cell to test your fixed names. It is not marked.

```python 1B: test your names (optional)
# Try creating each fixed variable here, for example:
# my_name = 1
```

### 1C: Declaring variables (3 marks)

Write code to declare the following variables.

(i) `a`, initialised to 17
(ii) `b`, initialised to 5
(iii) `total`, initialised to the sum of `a` and `b`
(iv) `gap`, initialised to the difference between `a` and `b`
(v) `whole_share`, initialised to the floor division (whole-number division) of `a` by `b`
(vi) `leftover`, initialised to `a` modulo `b` (the remainder when `a` is divided by `b`)

Print each variable to show that your code works.

```python 1C
# Write your code to declare the variables here

# (i)

# (ii)

# (iii)

# (iv)

# (v)

# (vi)

```

### 1D: Reading code (6 marks)

Explain what each line of the following code does, starting with line 4. Write each explanation as a comment at the end of its line. You can run the cell to check what it prints.

```python 1D
word = "loop"  # write your comments at the end of each line, like this one
# e.g. word is a string variable that stores the value "loop"

word = word * 3
word = word.upper()
size = len(word)
letters = list(word)
print(letters[5])
last = word[-1]
```

## Question 2: Expressions and If-Statements (15 marks)

### 2A: Cinema ticket program (10 marks)

A community cinema charges different prices for different ages. Write a program in the next cell that does the following.

1. Prints an instruction asking the user to enter their age in years.
2. Accepts input from the user and stores that input in a variable named `age_text`.
3. If the input is not a whole number, tells the user that they did not enter a whole number.
4. If the age is under 18, tells the user that they need a junior ticket, which costs €6.
5. If the age is from 18 to 64, tells the user that they need an adult ticket, which costs €10.
6. If the age is 65 or over, tells the user that they need a senior ticket, which costs €7.

You do not need to write a function. A script is enough. Run your program several times to test each case.

```python 2A
# Write your code here

```

### 2B: Choosing values (5 marks)

Choose values for `x`, `y` and `z` so that every one of the following expressions evaluates to `True`. Demonstrate your answer in the code cell below.

(i) `x + y < z`
(ii) `y - x == 2`
(iii) `x % 2 == 1`
(iv) `str(x) + str(y) == str(z)`

```python 2B
# Uncomment the next three lines and replace each ? with your value
# x = ?
# y = ?
# z = ?

# Print each expression to show that it is True
# print(x + y < z)
# print(y - x == 2)
# print(x % 2 == 1)
# print(str(x) + str(y) == str(z))
```

## Question 3: Loops and Lists (15 marks)

### 3A: Working with a list (8 marks)

Write code that does the following.

(i) Declares a list named `numbers` that contains the integers from 10 through 19.
(ii) Declares an integer `first` that takes the first value of `numbers`.
(iii) Declares a list `middle` that slices `numbers` to store the numbers 13, 14, 15 and 16.
(iv) Asks the user for a position, stores it as an integer in `position`, and then prints the element of `numbers` at that position.

```python 3A
# Write your code here

# (i)

# (ii)

# (iii)

# (iv)

```

### 3B: Infinite loops (2 marks)

What is an infinite loop? Describe one way that a programmer can make sure a `while` loop ends.

```answer 3B
```

### 3C: Guessing game (5 marks)

Write a program that keeps asking the user to guess the secret word `"python"` until they type it correctly. After each wrong guess, print `"Not quite, try again!"`. When the user guesses correctly, print how many guesses they needed.

```python 3C
# Write your code here

```

## Question 4: Functions (15 marks)

### 4A: Parts of a function (6 marks)

Study the following function. For each term below, give its name or value in this function, and explain what the term means.

```text
def shout_first_word(sentence: str) -> str:
    words = sentence.split()
    first = words[0]
    return first.upper() + "!"

print(shout_first_word("hello there friend"))
```

```fields 4A
Function name
Parameter(s)
Variable declaration(s)
Return statement
Function call
What would happen if the last line (the function call) were removed?
```

### 4B: Writing functions (9 marks)

Write the following functions with clear comments, and write tests to show that each function works. You can assume that every input has the correct type.

**(i) Longer word (4 marks).** Write a function named `longer_word` that takes two strings as arguments and returns whichever string is longer. If both strings have the same length, it returns the first string.

```python 4B (i): your function
# Write your function here

```

```python 4B (i): your tests
# Call your function and write your tests here

```

**(ii) Counting a letter (5 marks).** Write a function named `count_letter` with two arguments, `text` and `letter`. It must use a loop to count how many times `letter` appears in `text`, and return the count. Do not use the built-in `.count()` method.

```python 4B (ii): your function
# Write your function here

```

```python 4B (ii): your tests
# Call your function and write your tests here

```
