#!/bin/sh

# Run the tests without parallelization.
echo "running tests without parallelization ...";
python3 main.py examples/add_lists.zb 0 0;
python3 main.py examples/add_lists2.zb 0 0;
python3 main.py examples/small_kernel_conv.zb 0 0;
python3 main.py examples/not_parallelizable.zb 0 0;

# Run the add_lists test with parallelization.
echo "";
echo "running tests with parallelization ...";
python3 main.py examples/add_lists.zb 1 1;
python3 main.py examples/add_lists2.zb 1 1;
python3 main.py examples/small_kernel_conv.zb 1 1;
python3 main.py examples/not_parallelizable.zb 1 0;
