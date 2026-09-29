---
dewmark: 1
code: pdp-5n2927-practice-1
title: Practice Examination 1
module: Programming and Design Principles
module code: 5N2927
session: 2025–2026
institution: Dublin and Dún Laoghaire ETB
college: Dublin College Dundrum
kind: practice
total marks: 60
time allowed: 2 hours
code completion: on
python reference: yes
python time limit: 10 seconds
error hints: on
timer: shown
python from: this file
hand in: Save your answer file and your PDF, then upload both to the exam's assignment on Moodle. Show your invigilator the confirmation.
---

**Weighting:** 30% of the module (60 marks, divided by 2).  **Time allowed:** 2 hours.

This practice paper follows the structure of the final examination. Try it under exam conditions first, with the timer running. Then go back over any question that caused you trouble.

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

**(i)** Name three programming languages that are in wide use today.

```answer 1A (i)
```

**(ii)** Explain the difference between interpreted and compiled programming languages.

```answer 1A (ii)
```

**(iii)** Name two programming paradigms and describe each one briefly.

```answer 1A (iii)
```

### 1B: Variable declarations (3 marks)

Which of the following are valid variable declarations in Python? Fix each invalid one so that it becomes valid.

(i) `first-name = "Aoife"`
(ii) `level_5 = True`
(iii) `for = 10`
(iv) `_total = 0`
(v) `9lives = "cat"`
(vi) `module_code = "5N2927"`

```answer 1B
Valid:

Not valid:

My fixed versions:
```

```python exec 1B: test your declarations (not marked)
# Try your fixed declarations here. This cell is not marked.
```

### 1C: Declaring variables (3 marks)

Write code to declare the following variables.

(i) `a`, initialised to 19
(ii) `b`, initialised to 4
(iii) `division`, initialised to the result of dividing `a` by `b` (as a float)
(iv) `floor_division`, initialised to the integer (floor) division of `a` by `b`
(v) `power`, initialised to `a` raised to the power of `b`
(vi) `remainder`, initialised to `a` modulo `b` (the remainder when `a` is divided by `b`)

Print each variable to show that your code works.

```python exec 1C
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

```python exec 1D
city = "dublin"  # write your comments at the end of each line, like this one
# e.g. city is a string variable that stores the value "dublin"

city = city.title()
city = city + " " + "2026"
parts = list(city)
count = len(parts)
middle = parts[count // 2]
print(middle)
```

## Question 2: Expressions and If-Statements (15 marks)

### 2A: Divisibility checker (10 marks)

Create a program in the next cell that does the following.

1. Prints an instruction asking the user to enter a whole number between 1 and 100.
2. Accepts input from the user and stores that input in a variable named `user_number`.
3. If the input is not a valid whole number, tells the user that they did not enter a valid number.
4. If the number is less than 1 or greater than 100, tells the user that the number is out of range.
5. If the number is between 1 and 100 (inclusive), tells the user whether their number is divisible by both 2 and 5, by 2 only, by 5 only, or by neither.

You do not need to write a function. A script is enough.

```python exec 2A
# Write your code here

```

### 2B: Choosing values (5 marks)

Choose values for `a`, `b` and `c` so that every one of the following expressions evaluates to `True`. Demonstrate your answer in the code cell below.

(i) `a - b == c`
(ii) `a > b * c`
(iii) `c % b == 1`
(iv) `str(a) != str(b) + str(c)`

```python exec 2B
# Uncomment the next three lines and replace each ? with your value
# a = ?
# b = ?
# c = ?

# Print each expression to show that it is True
# print(a - b == c)
# print(a > b * c)
# print(c % b == 1)
# print(str(a) != str(b) + str(c))
```

## Question 3: Loops and Lists (15 marks)

### 3A: Working with a list (8 marks)

Write code that does the following.

(i) Declares a list with the odd numbers from 1 through 19 in the variable `odd_numbers`.
(ii) Declares an integer `last` that takes the value of the last element of `odd_numbers`.
(iii) Declares a list `subset` that slices `odd_numbers` to store the numbers 7, 9, 11 and 13.
(iv) Creates a new list `doubled` that contains every number in `odd_numbers` multiplied by 2.

```python exec 3A
# Write your code here

# (i)

# (ii)

# (iii)

# (iv)

```

### 3B: Nested loops (2 marks)

Describe a situation where you would use a nested loop. Give a brief example to illustrate your answer.

```answer 3B
```

### 3C: Multiples (5 marks)

Write a program that builds a list of all the numbers from 1 to 60 that are divisible by 4 or by 6 (or by both). Print the list, and then print how many numbers it contains.

```python exec 3C
# Write your code here

```

## Question 4: Functions (15 marks)

### 4A: Parts of a function (6 marks)

Study the following function. For each term below, give its name or value in this function, and explain what the term means.

```python
def count_capitals(text: str) -> int:
    total = 0
    for char in text:
        if char.isupper():
            total += 1
    return total

print(count_capitals("Dublin College Dundrum"))
```

```boxes 4A
Function name
Parameter(s)
Variable declaration(s)
Conditional statement
Return statement
Function call, and what it prints
```

### 4B: Writing functions (9 marks)

Write the following functions with clear comments, and write tests to show that each function works. You can assume that every input has the correct type.

#### (i) Same first and last (4 marks)

Write a function named `same_first_and_last` that takes a string as an argument. It returns `True` if the first and last characters are the same, ignoring capital letters, and `False` otherwise. For example, `"Anna"` and `"Level"` give `True`, and `"Dublin"` gives `False`.

```python exec 4B (i): your function
# Write your function here

```

```python exec 4B (i): your tests
# Call your function and write your tests here

```

#### (ii) Digits and letters (5 marks)

Write a function named `count_digits_and_letters` that takes a string as an argument. It returns a tuple with two values: the number of digits in the string, and the number of letters in the string. Spaces and other characters are not counted. For example, `count_digits_and_letters("Room 4B")` returns `(1, 5)`.

```python exec 4B (ii): your function
# Write your function here

```

```python exec 4B (ii): your tests
# Call your function and write your tests here

```

# Marking scheme

## Question 1

Topic:
Outcomes:

### 1A (draft)

### 1B (draft)

### 1C (draft)

### 1D (draft)

## Question 2

Topic:
Outcomes:

### 2A (draft)

### 2B (draft)

## Question 3

Topic:
Outcomes:

### 3A (draft)

### 3B (draft)

### 3C (draft)

## Question 4

Topic:
Outcomes:

### 4A (draft)

### 4B(i) (draft)

### 4B(ii) (draft)
