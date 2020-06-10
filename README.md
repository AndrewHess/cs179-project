# cs179-project

## Overview
The ```main.py``` file takes a .zb code file and a boolean for whether the code should be parallelized if it is possible. Then the code is converted to C++ (and CUDA, if parts are parallelized), a Makefile is generated, the code is compiled, and finally executed.

## Syntax
### Types
Every variable must be an integer, floating point number, string, or one dimensional array of one of those types. However, in the current version, strings should only be used as literals (for instance, to print), and floating point numbers are currently lacking many primitive functions, such as addition. Thus, most programs will only use ints, lists of ints, and literal strings. Lists can only contain elements a single type.

Types are specified as follows:
- Integer: ```int```
- Float: ```float```
- String: ```string```
- List of Integers: ```list int```
- List of Floats: ```list float```
- List of Strings: ```list string```

### Literals
Integer, float, and string literals can be specified as follows:
- ```(lit 5)```
- ```(lit 3.71)```
- ```(lit 'hello world!')```

Note that literal strings must be specified with single quotes rather than double quotes. There is currently no support for creating literal values of lists.


### Retrieving Variables
#### Non-list Variables
The value of non-list variables can be obtained via a ```get``` expression. For example, ```(get x)``` retieves the value of a variable ```x```.

#### List Variables
To retieve an element in a list, use the syntax ```(list_at <list> <index>)```. For example, you can retieve the 5th element in a list named ```lst``` via ```(list_at lst (lit 4))```. Note that lists are 0-indexed. The size of the a list ```lst``` can be obtained via ```(get lst.size)```.


### Creating Variables
#### Non-list Variables
Non-list variables are created with the syntax ```(val <type> <name> <value>)```. Thus, to create a floating point number named ```x``` with value 8.45, you could use ```(val float x (lit 8.45))```. The value can also be the value of a different variable. For example, ```(val float x (get y))``` corresponds to the C code ```float x = y```. Note that in this case, ```y``` must also be a float.

#### List Variables
Lists are created via the syntax ```(list <elem_type> <name> <size>)```. For example, a list named ```lst``` of 12 integers can be created via ```(list int lst (lit 12))```. Note that lists are not initialized upon creation.


### Calling Functions
Functions are called via the syntax ```(call <func_name> : <arg1_val> <arg2_val> ...)```. For example, a function named ```func``` that takes three integers can be called via ```(call func : (lit 0) (lit 45) (lit 12))```. A function that takes no arguments must still contain the colon, so it would be called via ```(call func2 :)```


### Setting Variables
#### Non-list variables
Non-list variables that have already been created can be set to a different value (with the same type as the variable's initial type) following the syntax ```(set <var_name> <new_value>)```. For example, ```(set x (lit 17))``` sets an integer variable ```x``` to 17.

#### List Variables
An element of a list can be set with the syntax ```(list_set <list_name> <index> <new_value>)```. For example, ```(list_set lst (lit 0) (lit 143))``` sets the first element of the integer list ```list``` to 143.
    

### Defining Functions
Functions are defined via the syntax ```(define <return_type> <name> : <arg1_type> <arg1_name> <arg2_type> <arg2_name> ... : <body_expr1> <body_expr2> ...)```. For example, a function named ```func``` that multiplies two input integers together, adds 3, and returns the result can be created via:
```
(define func : int x int y :
    (call + : (call * : (get x) (get y)) (get 3))
)
```
Note that the value of the final expression is always returned by a function, and there is no way to return before the end of a function.


### If Statements
If statemes are specified via the syntax ```(if <conditino> then <then1> <then2> ... else <else1> <else2> ...)```. For example, setting a variable ```x``` to 5 if ```x``` is initially odd and setting it to 3 otherwise can be achieved via
```
(if (call % : (get x) 2) then
    (set x (lit 5))
else
    (set x (lit 3))
)
```


### Loops
Loops can be created with the syntax ```(loop <init> <update> <test> do <expr1> <expr2> ...)```. For example, you can print 'hello world!' ten times via:
```
(loop (val int i (lit 0))
      (call < : (get i) (lit 10))
      (set i : (call + : (get i) (lit 1)))
do
    (call print : (lit 'hello world!'))
)
```
Sometimes it is beneficial to create a loop that is always executed sequentially, even if it could run in parallel without sacrificing the correctness of the result. A loop can be forced to be sequential by using the seq_loop keyword in place of the loop keyword. The rest of the syntax is identical.


## Primitive Functions
There are various primitive functions available for two integers. They are:
- ```+```
- ```-```
- ```*```
- ```/```
- ```%```
- ```>```
- ```>=```
- ```<```
- ```<=```
- ```==```
- ```!=```
- ```or```
- ```and```
- ```xor```

However, there is not currently support for similar functions for floating point numbers. Each of these primitive functions have the same meaning as they do in C, except for ```or```, ```and```, and ```xor```, which correspond to ```||```, ```&&```, and ```^``` in C respectively.

Printing follows the same method as is used in C, where you specify a format string and then provide additional arguments are required by the format string. For example, if ```x``` is an int with value 5, ```y``` is a float with value 4.51 and ```z``` is a string with value 'hello', then ```(call print : (lit '%s world! (%d) %f') (get z) (get x) (get y))\n``` would print the string 'hello world! (5) 4.51' and terminate with a newline.


## Demo
A demo of the project can be run via ```./demo.sh``` . This takes the
script ```examples/add_lists.zb``` and converts it into C++ and CUDA code, and
then compiles and runs the converted code and checks that the output is as
expected. The demo first runs the test without trying to parallelize any loops
and just converts the script to the equivalent C++ code. Afterwards, the test
is rerun but some loops are converted into parallel versions via CUDA to run on
the GPU.

After running the demo, the created C++ and CUDA files can be inspected in
the ```examples``` directory; only the parallelized versions will persist after
the demo, but the non-parallelized versions can be viewed by disabling the
second half of the demo script and then rerunning the demo.
