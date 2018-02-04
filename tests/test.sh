#!/usr/bin/env bats

@test "test dassie -d sh2008002926" {
  result="$(../bin/dassie -x -d sh2008002926)"
  expected="======================================================================
sh2008002926
         URL: http://id.loc.gov/authorities/subjects/sh2008002926.html
       label: Systems biology
  alt labels: (none)
    narrower: (none)
     broader: sh2003008355
     topmost: sh00007934, sh85118553
        note: (none)

======================================================================"
  [ "$result" = "$expected" ]
}

@test "test dassie -t sh2008002926 " {
  result="$(../bin/dassie -x -t sh2008002926)"
  expected="======================================================================
sh85118553: Science
└─ sh85076841: Life sciences
   └─ sh85014203: Biology
      └─ sh2003008355: Computational biology
         └─ sh2008002926: Systems biology

sh00007934: Science
└─ sh85076841: Life sciences
   └─ sh85014203: Biology
      └─ sh2003008355: Computational biology
         └─ sh2008002926: Systems biology

======================================================================"
  [ "$result" = "$expected" ]
}
