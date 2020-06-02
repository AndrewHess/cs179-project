#!/bin/sh

# Run the add_lists test without parallelization.
echo "running add_lists test without parallelization ..." &&
python3 main.py examples/add_lists.zb 0 &&
cd examples &&
make &&
time ./add_lists &&
echo "finished add_lists test without parallelization";
cd ..;

# Run the add_lists test with parallelization.
echo "running add_lists test with parallelization ..." &&
python3 main.py examples/add_lists.zb 1 &&
cd examples &&
make &&
time ./add_lists &&
echo "finished add_lists test with parallelization";
cd ..;
