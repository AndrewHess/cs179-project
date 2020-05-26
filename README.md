# cs179-project

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
