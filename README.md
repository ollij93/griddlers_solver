# Griddlers Solver

Griddlers, also known as nonograms, consist of a grid of colored tiles to be filled in by the solver.
For each row or column the blocks of each color are given including the colour and the length of the block.
Blocks of the same colour must have at least one space between them, 
blocks of different colour may or may not have spaces between them.

The simplist nonograms have only a single puzzle colour, as is seen in the example below.

## Before

```text
 .  .  .  .  .  .  .  .  .  .  .  .  .| 6, 6
 .  .  .  .  .  .  .  .  .  .  .  .  .| 1, 1
 .  .  .  .  .  .  .  .  .  .  .  .  .| 4, 4
 .  .  .  .  .  .  .  .  .  .  .  .  .| 4, 4
 .  .  .  .  .  .  .  .  .  .  .  .  .| 2, 1, 2, 1
 .  .  .  .  .  .  .  .  .  .  .  .  .| 4, 4
 .  .  .  .  .  .  .  .  .  .  .  .  .|
 .  .  .  .  .  .  .  .  .  .  .  .  .| 3
 .  .  .  .  .  .  .  .  .  .  .  .  .| 3
 .  .  .  .  .  .  .  .  .  .  .  .  .| 3
 .  .  .  .  .  .  .  .  .  .  .  .  .| 1, 1
 .  .  .  .  .  .  .  .  .  .  .  .  .| 1, 1
 .  .  .  .  .  .  .  .  .  .  .  .  .|11
 .  .  .  .  .  .  .  .  .  .  .  .  .| 7
 .  .  .  .  .  .  .  .  .  .  .  .  .| 1
---------------------------------------
 2  1  1  1  1  1  3  2  1  1  1  1  1|
       4  4  2  4  2  3  3  4  4  2  4|
       3  1  1  2     3  2  2  2  1  3|
             2                    1   |
```

## After

```text
 #  #  #  #  #  #     #  #  #  #  #  #| 6, 6
 #                    #               | 1, 1
       #  #  #  #           #  #  #  #| 4, 4
       #  #  #  #           #  #  #  #| 4, 4
       #  #     #           #  #     #| 2, 1, 2, 1
       #  #  #  #           #  #  #  #| 4, 4
                                      |
                   #  #  #            | 3
                   #  #  #            | 3
                   #  #  #            | 3
       #                             #| 1, 1
       #                             #| 1, 1
       #  #  #  #  #  #  #  #  #  #  #|11
             #  #  #  #  #  #  #      | 7
                      #               | 1
---------------------------------------
 2  1  1  1  1  1  3  2  1  1  1  1  1|
       4  4  2  4  2  3  3  4  4  2  4|
       3  1  1  2     3  2  2  2  1  3|
             2                    1   |
```

This griddlers solver implements several algorithms to solve a griddler line-by-line.
It is expected to work for all single-coloured griddlers, but there are known limitations that prevent some multi-coloured griddlers from being solved.

## griddlers.net

http://www.griddlers.net/

This site is my prefered place for solving puzzles and is where the puzzles for this solver are loaded from.
Puzzles are loaded from their ID number as seen below:

```bash
python3 -m griddlers_solver 250679
```

This command loads and solves the puzzle shown above.
