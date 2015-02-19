graph [
  is_directed 0
  node [
    id 3
    label "assemblage-3"
    xcoord 6
    ycoord 7
  ]
  node [
    id 4
    label "assemblage-4"
    xcoord 9
    ycoord 10
  ]
  node [
    id 5
    label "assemblage-5"
    xcoord 9
    ycoord 4
  ]
  edge [
    source 5
    target 3
    weight 1
    normalized_weight 0.1
  ]
  edge [
    source 5
    target 4
    weight 3
    normalized_weight 0.3
  ]
  edge [
    source 3
    target 4
    weight 3
    normalized_weight 0.3
  ]
]