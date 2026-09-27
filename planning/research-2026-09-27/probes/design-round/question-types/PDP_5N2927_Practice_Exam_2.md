---
exam_id: pdp-5n2927-practice-2
title: Practice Examination 2
module: Programming and Design Principles 5N2927
session: 2025–2026
institution: Dublin and Dún Laoghaire ETB
college: Dublin College Dundrum
kind: practice
total_marks: 60
duration_minutes: 120
allow_completion: true
show_reference: true
reference_theory: false
time_limit_seconds: 10
error_hints: true
---

# Programming and Design Principles 5N2927: Practice Examination 2

**Weighting:** 30% of the module (60 marks, divided by 2).  **Time allowed:** 2 hours.

This second practice paper follows the same structure as the final examination, with new problems. Some questions ask you to handle input that is wrong or out of range, so test your programs with bad input as well as good input.

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

**(i)** Low-level programming languages come in two main kinds. Name both kinds.

```answer 1A (i)
```

**(ii)** Who is often described as the first computer programmer? Name the machine that this person wrote a program for.

```answer 1A (ii)
```

**(iii)** What is pseudo-code, and why do programmers write it before they write real code?

```answer 1A (iii)
```

### 1B: Variable names (3 marks)

Which of the following are permitted as variable names in Python? Rewrite each one that is not permitted so that it becomes a permitted name.

(i) `my variable`
(ii) `myVariable`
(iii) `total$`
(iv) `while`
(v) `level5`
(vi) `5level`

```answer 1B
Permitted:

Not permitted:

My fixed versions:
```

```python 1B: test your names (optional)
# Try creating each fixed variable here. This cell is not marked.
```

### 1C: Declaring variables (3 marks)

Write code to declare the following variables.

(i) `p`, initialised to 9
(ii) `q`, initialised to 2
(iii) `product`, initialised to `p` multiplied by `q`
(iv) `true_division`, initialised to `p` divided by `q` (as a float)
(v) `squared`, initialised to `p` raised to the power of `q`
(vi) `is_bigger`, initialised to a comparison that is `True` when `p` is greater than `q`

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
code = "5N2927"  # write your comments at the end of each line, like this one
# e.g. code is a string variable that stores the value "5N2927"

code = code.lower()
letter = code[1]
digits = code[2:]
number = int(digits)
number = number + 1
print(code + "-" + str(number))
```

## Question 2: Expressions and If-Statements (15 marks)

### 2A: Grade calculator (10 marks)

QQI awards grades from a percentage result. Write a program in the next cell that does the following.

1. Prints an instruction asking the user to enter their result as a whole-number percentage.
2. Accepts input from the user and stores that input in a variable named `score_text`.
3. If the input is not a whole number, tells the user that they did not enter a whole number.
4. If the number is below 0 or above 100, tells the user that a percentage must be between 0 and 100.
5. Otherwise, tells the user their grade: **Distinction** for 80 to 100, **Merit** for 65 to 79, **Pass** for 50 to 64, and **Unsuccessful** below 50.

You do not need to write a function. A script is enough. Test the boundaries, such as 49, 50, 64 and 65.

```python 2A
# Write your code here

```

### 2B: Choosing values (5 marks)

Choose values for `p`, `q` and `r` so that every one of the following expressions evaluates to `True`. Demonstrate your answer in the code cell below.

(i) `p // q == r`
(ii) `p % q != 0`
(iii) `not (p < r)`
(iv) `len(str(p)) == 2`

```python 2B
# Uncomment the next three lines and replace each ? with your value
# p = ?
# q = ?
# r = ?

# Print each expression to show that it is True
# print(p // q == r)
# print(p % q != 0)
# print(not (p < r))
# print(len(str(p)) == 2)
```

## Question 3: Loops and Lists (15 marks)

### 3A: A week of temperatures (8 marks)

Write code that does the following.

(i) Declares a list named `temps` that stores these seven daily temperatures in order: 14, 17, 12, 19, 21, 16, 13.
(ii) Declares a variable `highest` that uses a built-in function to store the largest value in `temps`.
(iii) Declares a list `midweek` that slices `temps` to store the values 12, 19 and 21.
(iv) Uses a loop to build a new list `warm_days` that contains only the temperatures above 15, and prints it.

```python 3A
# Write your code here

# (i)

# (ii)

# (iii)

# (iv)

```

### 3B: For and while (2 marks)

What is the difference between a `for` loop and a `while` loop? Give an example of a task where you would use a `while` loop but not a `for` loop.

```answer 3B
```

### 3C: Countdown (5 marks)

Write a program that keeps asking the user for a starting number until they enter a whole number greater than 0. The program then counts down from that number to 1, printing each number on its own line, and finally prints `"Lift off!"`.

```python 3C
# Write your code here

```

## Question 4: Functions (15 marks)

### 4A: Parts of a function (6 marks)

Study the following function. For each term below, give its name or value in this function, and explain what the term means.

```text
def make_username(first: str, last: str, year: int = 2026) -> str:
    initial = first[0].lower()
    surname = last.lower()
    return initial + surname + str(year)[-2:]

print(make_username("Grace", "Hopper"))
```

```fields 4A
Function name
Parameter(s)
Default value, and what it means
Variable declaration(s)
Return statement
Function call, and what it prints
```

### 4B: Writing functions (9 marks)

Write the following functions with clear comments, and write tests to show that each function works. You can assume that every input has the correct type.

**(i) Both even (4 marks).** Write a function named `both_even` that takes two integers as arguments. It returns `True` when both numbers are even, and `False` otherwise.

```python 4B (i): your function
# Write your function here

```

```python 4B (i): your tests
# Call your function and write your tests here

```

**(ii) Filling with dots (5 marks).** Write a function named `fill_with_dots` with two arguments, `text` and `width`. It uses a loop to add a full stop (`.`) to the end of `text` until the text is `width` characters long, and then returns the result. If `text` is already `width` characters or longer, the function returns it unchanged. For example, `fill_with_dots("Hi", 5)` returns `"Hi..."`.

```python 4B (ii): your function
# Write your function here

```

```python 4B (ii): your tests
# Call your function and write your tests here

```
