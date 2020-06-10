# cs179-project

## Overview
The ```main.py``` file takes a .zb code file and a boolean for whether the code should be parallelized if it is possible. Then the code is converted to C++ (and CUDA, if parts are automatically parallelized), a Makefile is generated, the code is compiled, and finally executed.


## Motivation
While running code on a GPU can be very beneficial due to the potential speedup, translating sequential code into CUDA code to actually run a parallel job on a GPU can be tedious and error prone. This project automatically converts loops that satisfy certain parallelization requirements into their parallel equivalent so that the programmer is freed from the burden of checking the correctness of the basic conversions from CPU to GPU code. Additionally, writing sequential code is often easier and faster than writing parallelized code, so automatically converting the programmer's sequential code into CUDA as appropriate saves the programmer time.


## Demo
A demo of the project can be run via ```./demo.sh``` . This runs the following files in the examples directory:
- ```add_lists.zb```
- ```add_lists2.zb```
- ```small_kernel_conv.zb```
- ```not_parallelizable.zb```

All of these programs are run first without parallelization and then with attempted parallelization. The demo script ensures that all of the programs except for ```not_parallelizable.zb``` are in fact parallelized when they are run with attempted parallelization.

The output of running ```./demo.sh``` is:
```
running tests without parallelization ...
add_lists test passed!
add_lists2 test passed!
small_kernel_conv test passed!
not_parallelizable passed!

running tests with parallelization ...
add_lists test passed!
add_lists2 test passed!
small_kernel_conv test passed!
not_parallelizable passed!
```

The ```add_lists.zb``` and ```add_lists2.zb``` tests both generate two random lists (with the same length) of integers and then add the lists together into a third list and make sure that the result is the same as the what the CPU code obtained. The ```small_kernel_conv.zb``` test generates a large random list of integers and a small random list of integers and then convolves them, and checks that the result is the same as obtained by the CPU code. The ```not_parallelizable.zb``` test generates the first 40 fibonacci numbers in a list, but the demo script ensures that this script is not parallelized even when attempted parallelization is turned on. The script is not able to be parallelized because generating each consecutive element in the list requires that the previous two elements are correct.

After running the demo, the created C++ and CUDA files can be inspected in
the ```examples``` directory; only the parallelized versions will persist after
the demo, but the non-parallelized versions can be viewed by disabling the
second half of the demo script and then rerunning the demo.


## Algorithms Overview
There are three main tasks required to translate the provided code into equivalent C++ and CUDA code: parsing, parallelization analysis, and code generation.

### Parsing
Due to the relative simplicity of the language's syntax, parsing is fairly straightforward. The first word of each expression identifies what type of expression it is, which specifies how the rest of the expression should be parsed (i.e. what other elements should be in the expression for it to be a valid expression).

### Parallelization Analysis
Currently the only expressions that are considered for parallelization are loops. The parallelization requirements are more strict that is necessary because it is a relatively easy way to ensure that parallelizing the loop will not break the loop's functionality, which is a more severe outcome than not parallelizing a loop that is able to be parallelized. Any loop that is parallelized must meet all of the following requirements:

- The loop was specified with the ```loop``` keyword rather than the ```seq_loop``` keyword. The ```seq_loop``` keyword is useful for checking the integrity of GPU output against CPU output for testing purposes, and is also useful when the benefits of running the loop in parallel would be outweighed by the overhead of transfering the data to and from the GPU.
- The loop test used to determine when the loop terminates is of the form ```<index> <inequality> <end_val>``` (```<index>``` and ```<end_val>``` can be switched) where ```<inequality>``` is one of <, <=, >, >=, or !=.
- The loop update indrements or decrements the loop index by 1 each iteration, and the body of the loop does not update the loop index. This, together with the previous requirement, gives a simple means of determining the number of loop iterations so that the correct number of GPU threads can be invoked.
- The body of the loop does not set two different elements of the same loop. While not always the case, it is possible that parallelizing such a loop with produce different output because two different iterations of the loop may set the same element, but on a GPU there are no guarantees about which set would occur first.
- The body of the loop does not both set an element of a list and get a different element of that same list. Again, while not always the case, it is possible that parallelizing such a looo would lead to data integrity issues becuase the set value may rely on previous iterations setting other elements of the list.
- The loop body does not set any variable that is created outside of the loop. The reasoning for this restriction is the same reasoning for why two iterations are not allowed to set the same list element.

If the analyzer finds that a particular loop is parallelizable, it determines the name of the index variable, the start and end values of the index variable, the variables used by the loop body but created outside of the loop (so those variables can be copied to the GPU), and the body of the loop, so that the code generator can both generate the CUDA kernel code and setup the calling interface from the CPU to the GPU code.

### Code Generation
Generating the C++ code is relatively straightforward, as all expressions have been parsed and converted into parallelized versions if necessary. Additionally, all of the non-parallelized expressions have a straightforward translation into C++. The only slight complication is that the language stores the length of the list when a list is created, so lists are represented by structs containing the number of elements in the list and a pointer to the first element, rather than the pointer alone. In order to avoid complications with ```malloc()``` and ```free()```, all C++ arrays are created on the stack and connot be returned from a function.

Generating the GPU kernel code is also fairly simple. The thread index starts at ```blockIdx.x * blockDim.x + threadIdx.x + <start_index>```, where ```<start_index>``` is the lowest value of the index, as determined by the analyzer, and the thread loops until the index meets or exceeds the maximum index value of the loop (also determined by the analyzer), which each iteration increasing the thread index by ```gridDim.x * blockDim.x```. The body of this loop is directly copied from the body of the original non-parallelized loop (just converted to C++).

Generating the interface for the CPU code to call the GPU code is a little tedious, but not terribly difficult. The code generator already knows which variables are need to be passed to the kernel function, as this list of variables is provided by the analyzer. Non-list variables that are required are simply passed as arguments, as they will not be updated by the loop (if they were updated, the current anaylizer would not allow the loop to be parallelized). Required list variables are just copied to the GPU and then copied back to the appropriate list after the kernel finished in case the lists were updated.

The code generator also produces C++ and CUDA header files, as well as a Makefile. The Makefile provides both a ```clean``` target for removing the object and executable files and a ```full_clean``` target which removes all generated code, including the all C++ and CUDA code as well as the Makefile itself, as all of these files were generated.


## GPU Optimizations
In the current version of the project, there are no GPU optimizations; shared memory is not used, warp divergence is not detected or avoided, and global accesses are not necessarily coalesced. This lack of optimization is due to the difficulty of detecting and then avoiding these problems in a way that does not affect the functionality of the original user specified sequential loop. Due to these limitations, it is recommended that the output C++ and CUDA files are used as a starting point for the programmer to further optimize manually.


## Code Structure
The most important files are ```main.py```, ```parser.py```, ```analyzer.py```, ```generator.py```,  ```demo.sh```, and the example programs in the ```examples``` directory. As described above, the parser, analyzer, and generator are responsible for parsing the input code, determining whether loops can be parallelized, and outputing equivalent C++ and CUDA code as necessary along with a Makefile. The ```main.py``` program combines these tasks to translate a given code file into equivalent C++ and CUDA code, build an executable, and run the executable. The demo script then invokes the main program several times on the example scripts to ensure that they all pass.

## Running a Single Program
The ```main.py``` program has the usage ```main.py <code_file> <parallelize> [should_parallelize]```, where ```<code_file>``` specifies the .zb code to translate, ```<parallelize>``` is either 0 (do not parallelize the code) or 1 (parallelize the code if possible), and ```[should_parallelize]``` is also 0 or 1 and the test fails if its value disagrees with whether the provided code actually was parallelized (```should_parallelize``` is mainly useful for testing).

As an example, the ```examples/add_lists.zb``` example can be run with parallelization via ```python3 main.py examples/add_lists.zb 1```.

If a given script is not parallelized either becuase the main program was invoked with a specification of no parallelization or because the program could not be parallelized, no CUDA code is generated and the Makefile does not make the executable depend on CUDA code. This has the benefit that non-parallelized code can be run on machines that do no have CUDA (so long as the machine has python3 and gcc).


## Language Syntax
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
Sometimes it is beneficial to create a loop that is always executed sequentially, even if it could run in parallel without sacrificing the correctness of the result. A loop can be forced to be sequential by using the ```seq_loop``` keyword in place of the loop keyword. The rest of the syntax is identical.


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

